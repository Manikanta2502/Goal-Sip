from flask import Flask, render_template, request, jsonify
from flask_lambda import FlaskLambda
import math
import os


app = Flask(__name__, template_folder=os.path.abspath('../templates'),
            static_folder=os.path.abspath('../static'))



# (Your existing Flask code goes here unchanged)

# Functions for financial calculations
def calculate_sip(principal, rate, time):
    monthly_rate = rate / 12 / 100
    n = time * 12
    future_value = principal * (((1 + monthly_rate)**n - 1) / monthly_rate) * (1 + monthly_rate)
    return future_value

def calculate_required_investment(target_amount, rate, time):
    monthly_rate = rate / 12 / 100
    n = time * 12
    required_investment = target_amount / (((1 + monthly_rate)**n - 1) / monthly_rate) * (1 + monthly_rate)
    return required_investment

def calculate_step_up_sip(principal, rate, time, step_up_percent):
    monthly_rate = rate / 12 / 100
    n = time * 12
    future_value = 0
    for i in range(n):
        monthly_principal = principal * (1 + step_up_percent / 100)**(i // 12)
        future_value += monthly_principal * (1 + monthly_rate)**(n - i)
    return future_value

def calculate_required_step_up_investment(target_amount, rate, time, step_up_percent):
    monthly_rate = rate / 12 / 100
    n = time * 12
    low, high = 0, target_amount
    tolerance = 1
    while low <= high:
        mid = (low + high) / 2
        future_value = calculate_step_up_sip(mid, rate, time, step_up_percent)
        if abs(future_value - target_amount) < tolerance:
            return mid
        elif future_value < target_amount:
            low = mid + 1
        else:
            high = mid - 1
    return (low + high) / 2

def round_to_nearest_hundred(number):
    return round(number / 100) * 100

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    salary = float(data['salary'])
    expenses = float(data['expenses'])
    wants = float(data['wants']) if data['wants'] else 0
    expected_return = float(data['expected_return'])
    step_up_percent = float(data['step_up']) if data['step_up'] else 0
    goals = data['goals']

    results = {'regular_sip': [], 'step_up_sip': []}
    total_regular = 0
    total_step_up = 0

    for goal in goals:
        goal_name = goal['name']
        target_amount = float(goal['amount'])
        time = int(goal['time'])

        required_investment = calculate_required_investment(target_amount, expected_return, time)
        rounded_investment = round_to_nearest_hundred(required_investment)
        total_regular += required_investment

        results['regular_sip'].append({
            'name': goal_name,
            'investment': rounded_investment
        })

        required_investment_step_up = calculate_required_step_up_investment(target_amount, expected_return, time, step_up_percent)
        rounded_investment_step_up = round_to_nearest_hundred(required_investment_step_up)
        total_step_up += required_investment_step_up

        results['step_up_sip'].append({
            'name': goal_name,
            'investment': rounded_investment_step_up
        })

    results['totals'] = {
        'total_regular': round_to_nearest_hundred(total_regular),
        'total_step_up': round_to_nearest_hundred(total_step_up),
        'remaining_regular': round_to_nearest_hundred(salary - (expenses + wants + total_regular)),
        'remaining_step_up': round_to_nearest_hundred(salary - (expenses + wants + total_step_up))
    }

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
