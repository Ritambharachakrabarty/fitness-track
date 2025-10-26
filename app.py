from flask import send_from_directory, Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv
import pymysql.cursors  # Still needed for DictCursor

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# MySQL configurations
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST', 'sql12.freesqldatabase.com')
app.config['MYSQL_PORT'] = int(os.environ.get('DB_PORT', '3306'))
app.config['MYSQL_DB'] = os.environ.get('DB_NAME', 'sql12804493')
app.config['MYSQL_USER'] = os.environ.get('DB_USER', 'sql12804493')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD', 'nBmLGyzpMb')
app.config['MYSQL_CHARSET'] = 'utf8mb4'
app.config['MYSQL_CONNECT_TIMEOUT'] = 10
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # For dictionary-based results

# Initialize MySQL
mysql = MySQL(app)

@app.route('/api/goals', methods=['GET'])
def get_goals():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM goals ORDER BY created_at DESC')
        goals = cursor.fetchall()
        print(f"Goals retrieved: {goals}")
        return jsonify(goals)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load goals'}), 500
    finally:
        cursor.close()

@app.route('/api/goals', methods=['POST'])
def add_goal():
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO goals (goal_type, target_value, unit, deadline, status) VALUES (%s, %s, %s, %s, %s)',
                       (data['goal_type'], data['target_value'], data.get('unit'),
                        data.get('deadline'), data.get('status', 'Pending')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Goal added successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error adding goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        cursor.close()

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM workouts ORDER BY created_at DESC')
        workouts = cursor.fetchall()
        print(f"Workouts retrieved: {workouts}")
        return jsonify(workouts)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load workouts'}), 500
    finally:
        cursor.close()

@app.route('/api/workouts', methods=['POST'])
def add_workout():
    try:
        data = request.json
        app.logger.info(f"Received workout data: {data}")
        if not all(key in data for key in ['date', 'type', 'duration', 'calories']):
            return jsonify({'error': 'Missing required fields'}), 400
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO workouts (date, type, duration, calories, intensity, distance, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['type'], data['duration'], data['calories'],
                        data.get('intensity'), data.get('distance'), data.get('notes')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Workout added successfully'}), 201
    except Exception as db_error:
        app.logger.error(f"Database error: {db_error}")
        return jsonify({'error': f'Database error: {db_error}'}), 500
    except (KeyError, TypeError) as data_error:
        app.logger.error(f"Data error: {data_error}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        cursor.close()

@app.route('/api/meals/daily/<date>', methods=['GET'])
def get_daily_meals(date):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM meals WHERE date = %s ORDER BY created_at ASC', (date,))
        meals = cursor.fetchall()
        cursor.execute('SELECT SUM(calories) as calories, SUM(protein) as protein, SUM(carbs) as carbs, SUM(fats) as fats FROM meals WHERE date = %s', (date,))
        totals = cursor.fetchone()
        return jsonify({
            'meals': meals,
            'totals': {
                'calories': totals['calories'] or 0,
                'protein': totals['protein'] or 0,
                'carbs': totals['carbs'] or 0,
                'fats': totals['fats'] or 0
            }
        })
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load meals'}), 500
    finally:
        cursor.close()

@app.route('/api/meals', methods=['POST'])
def add_meal():
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO meals (date, meal_type, food_name, calories, protein, carbs, fats, portion_size, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['meal_type'], data['food_name'], data['calories'],
                        data.get('protein', 0), data.get('carbs', 0), data.get('fats', 0),
                        data.get('portion_size'), data.get('notes')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Meal added successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error adding meal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        cursor.close()

@app.route('/api/calorie-goals/<date>', methods=['GET'])
def get_calorie_goal(date):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM calorie_goals WHERE date = %s', (date,))
        goal = cursor.fetchone()
        return jsonify(goal if goal else None)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load calorie goal'}), 500
    finally:
        cursor.close()

@app.route('/api/calorie-goals', methods=['POST'])
def set_calorie_goal():
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO calorie_goals (date, daily_goal, achieved) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE daily_goal = %s, achieved = %s',
                       (data['date'], data['daily_goal'], data.get('achieved', 0),
                        data['daily_goal'], data.get('achieved', 0)))
        mysql.connection.commit()
        return jsonify({'message': 'Calorie goal set successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error setting calorie goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        cursor.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM workouts')
        total_workouts = cursor.fetchone()['count']
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM workouts')
        total_calories_burned = cursor.fetchone()['total']
        cursor.execute('SELECT IFNULL(SUM(duration), 0) as total FROM workouts')
        total_duration = cursor.fetchone()['total']
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM meals')
        total_calories_consumed = cursor.fetchone()['total']
        return jsonify({
            'total_workouts': total_workouts,
            'total_calories_burned': total_calories_burned,
            'total_duration': total_duration,
            'total_calories_consumed': total_calories_consumed,
            'net_calories': total_calories_consumed - total_calories_burned
        })
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load stats'}), 500
    finally:
        cursor.close()

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
