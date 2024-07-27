from flask import Flask, request, redirect, url_for, render_template_string
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'C:/Users/hp/Desktop/truck Detail'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

EXCEL_FILE = os.path.join(UPLOAD_FOLDER, 'vehicle_data.xlsx')

# Function to save data to Excel
def save_to_excel(data):
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_new = pd.DataFrame(data, index=[0])
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df = pd.DataFrame(data, index=[0])
    df.to_excel(EXCEL_FILE, index=False)

# Function to check if a truck number already exists
def truck_number_exists(truck_number):
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        return truck_number in df_existing['Vehicle Number'].values
    return False

# Function to validate date
def validate_date(date_str):
    try:
        # Check format and parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Ensure the date is not before January 1, 2024
        if date_obj < datetime(2024, 1, 1):
            return False
        return True
    except ValueError:
        return False

@app.route('/')
def upload_form():
    message = request.args.get('message', '')
    return f'''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vehicle Data Entry</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="text-center">Vehicle Data Entry</h2>
            <form method="post" enctype="multipart/form-data" action="/upload">
                <div class="form-group">
                    <label for="vehicleNumber">Vehicle Number:</label>
                    <input type="text" class="form-control" id="vehicleNumber" name="vehicleNumber" required>
                </div>
                <div class="form-group">
                    <label for="unladenWeight">Unladen Weight:</label>
                    <input type="text" class="form-control" id="unladenWeight" name="unladenWeight" required>
                </div>
                <div class="form-group">
                    <label for="loadenWeight">Loaden Weight:</label>
                    <input type="text" class="form-control" id="loadenWeight" name="loadenWeight" required>
                </div>
                <div class="form-group">
                    <label for="insuranceExpiry">Insurance Expiry Date:</label>
                    <input type="date" class="form-control" id="insuranceExpiry" name="insuranceExpiry" required>
                </div>
                <div class="form-group">
                    <label for="fitnessExpiry">Fitness Expiry Date:</label>
                    <input type="date" class="form-control" id="fitnessExpiry" name="fitnessExpiry" required>
                </div>
                <div class="form-group">
                    <label for="pollutionExpiry">Pollution Expiry Date:</label>
                    <input type="date" class="form-control" id="pollutionExpiry" name="pollutionExpiry" required>
                </div>
                <div class="form-group">
                    <label for="permitExpiry">Permit Expiry Date:</label>
                    <input type="date" class="form-control" id="permitExpiry" name="permitExpiry" required>
                </div>
                <div class="form-group">
                    <label for="pdfFile">Upload PDF (max 5MB):</label>
                    <input type="file" class="form-control-file" id="pdfFile" name="pdfFile" accept="application/pdf" required>
                </div>
                <button type="submit" class="btn btn-success btn-block">Submit</button>
                {f'<div class="alert alert-danger mt-3" role="alert">{message}</div>' if message else ''}
            </form>

            <h2 class="text-center mt-5">Generate Report</h2>
            <form method="get" action="/report">
                <div class="form-group">
                    <label for="reportVehicleNumber">Vehicle Number:</label>
                    <input type="text" class="form-control" id="reportVehicleNumber" name="vehicleNumber" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Generate Report</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    vehicle_number = request.form['vehicleNumber']
    
    if truck_number_exists(vehicle_number):
        return redirect(url_for('upload_form', message='Truck Number already exists'))
    
    if 'pdfFile' not in request.files:
        return redirect(url_for('upload_form', message='No file part'))
    
    file = request.files['pdfFile']
    if file.filename == '':
        return redirect(url_for('upload_form', message='No selected file'))
    
    if file and file.filename.endswith('.pdf') and file.mimetype == 'application/pdf':
        insurance_expiry = request.form['insuranceExpiry']
        fitness_expiry = request.form['fitnessExpiry']
        pollution_expiry = request.form['pollutionExpiry']
        permit_expiry = request.form['permitExpiry']
        
        # Validate date fields
        if not all(validate_date(date) for date in [insurance_expiry, fitness_expiry, pollution_expiry, permit_expiry]):
            return redirect(url_for('upload_form', message='All dates must be in yyyy-mm-dd format and not earlier than 2024-01-01'))
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{vehicle_number}.pdf")
        try:
            file.save(file_path)
            
            # Save form data to Excel
            data = {
                'Vehicle Number': vehicle_number,
                'Unladen Weight': request.form['unladenWeight'],
                'Loaden Weight': request.form['loadenWeight'],
                'Insurance Expiry Date': insurance_expiry,
                'Fitness Expiry Date': fitness_expiry,
                'Pollution Expiry Date': pollution_expiry,
                'Permit Expiry Date': permit_expiry,
                'File Path': file_path
            }
            save_to_excel(data)
            
            return redirect(url_for('upload_form', message='File and data successfully uploaded'))
        except Exception as e:
            return redirect(url_for('upload_form', message=f"Error saving file: {e}"))
    else:
        return redirect(url_for('upload_form', message='Invalid file format'))

@app.route('/report', methods=['GET'])
def report():
    vehicle_number = request.args.get('vehicleNumber')
    if not vehicle_number:
        return redirect(url_for('upload_form', message='Vehicle Number is required for report'))

    if truck_number_exists(vehicle_number):
        df = pd.read_excel(EXCEL_FILE)
        data = df[df['Vehicle Number'] == vehicle_number].to_dict(orient='records')
        if data:
            data = data[0]
            return f'''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Vehicle Report</title>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
            </head>
            <body>
                <div class="container mt-5">
                    <h2 class="text-center">Vehicle Report</h2>
                    <table class="table table-bordered">
                        <tr><th>Vehicle Number</th><td>{data.get('Vehicle Number')}</td></tr>
                        <tr><th>Unladen Weight</th><td>{data.get('Unladen Weight')}</td></tr>
                        <tr><th>Loaden Weight</th><td>{data.get('Loaden Weight')}</td></tr>
                        <tr><th>Insurance Expiry Date</th><td>{data.get('Insurance Expiry Date')}</td></tr>
                        <tr><th>Fitness Expiry Date</th><td>{data.get('Fitness Expiry Date')}</td></tr>
                        <tr><th>Pollution Expiry Date</th><td>{data.get('Pollution Expiry Date')}</td></tr>
                        <tr><th>Permit Expiry Date</th><td>{data.get('Permit Expiry Date')}</td></tr>
                        <tr><th>File Path</th><td>{data.get('File Path')}</td></tr>
                    </table>
                    <a href="/" class="btn btn-primary">Back</a>
                </div>
            </body>
            </html>
            '''
        else:
            return redirect(url_for('upload_form', message='No data found for the given Vehicle Number'))
    else:
        return redirect(url_for('upload_form', message='Vehicle Number does not exist'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
