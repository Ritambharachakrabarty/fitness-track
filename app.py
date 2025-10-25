from flask import send_from_directory, Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
from dotenv import load_dotenv

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
app.config['MYSQL_CONNECTION_TIMEOUT'] = 10

# Create a connection pool or manage connection manually
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        db=app.config['MYSQL_DB'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        charset=app.config['MYSQL_CHARSET'],
        connect_timeout=app.config['MYSQL_CONNECTION_TIMEOUT']
    )

@app.route('/api/goals', methods=['GET'])
def get_goals():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM goals ORDER BY created_at DESC')
        goals = cursor.fetchall()
        print(f"Goals retrieved: {goals}")
        return jsonify(goals)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load goals'}), 500
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/goals', methods=['POST'])
def add_goal():
    connection = None
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO goals (goal_type, target_value, unit, deadline, status) VALUES (%s, %s, %s, %s, %s)',
                       (data['goal_type'], data['target_value'], data.get('unit'),
                        data.get('deadline'), data.get('status', 'Pending')))
        connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Goal added successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error adding goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM workouts ORDER BY created_at DESC')
        workouts = cursor.fetchall()
        print(f"Workouts retrieved: {workouts}")
        return jsonify(workouts)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load workouts'}), 500
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/workouts', methods=['POST'])
def add_workout():
    connection = None
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO workouts (date, type, duration, calories, intensity, distance, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['type'], data['duration'], data['calories'],
                        data.get('intensity'), data.get('distance'), data.get('notes')))
        connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Workout added successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error adding workout: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/meals/daily/<date>', methods=['GET'])
def get_daily_meals(date):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
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
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/meals', methods=['POST'])
def add_meal():
    connection = None
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO meals (date, meal_type, food_name, calories, protein, carbs, fats, portion_size, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['meal_type'], data['food_name'], data['calories'],
                        data.get('protein', 0), data.get('carbs', 0), data.get('fats', 0),
                        data.get('portion_size'), data.get('notes')))
        connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Meal added successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error adding meal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/calorie-goals/<date>', methods=['GET'])
def get_calorie_goal(date):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM calorie_goals WHERE date = %s', (date,))
        goal = cursor.fetchone()
        return jsonify(goal if goal else None)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load calorie goal'}), 500
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/calorie-goals', methods=['POST'])
def set_calorie_goal():
    connection = None
    try:
        data = request.json
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO calorie_goals (date, daily_goal, achieved) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE daily_goal = %s, achieved = %s',
                       (data['date'], data['daily_goal'], data.get('achieved', 0),
                        data['daily_goal'], data.get('achieved', 0)))
        connection.commit()
        return jsonify({'message': 'Calorie goal set successfully'}), 201
    except (KeyError, TypeError, Exception) as e:
        print(f"Error setting calorie goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM workouts')
        total_workouts = cursor.fetchone()[0]
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM workouts')
        total_calories_burned = cursor.fetchone()[0]
        cursor.execute('SELECT IFNULL(SUM(duration), 0) as total FROM workouts')
        total_duration = cursor.fetchone()[0]
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM meals')
        total_calories_consumed = cursor.fetchone()[0]
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
        if connection:
            cursor.close()
            connection.close()

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)