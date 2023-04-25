import firebase_admin
from appscript.defaultterminology import elements
from flask import Flask, render_template, request, redirect, url_for, session
from firebase_admin import credentials, firestore, initialize_app
from holoviews.plotting.mpl import styles
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
#from google.cloud import firestore
from vsm import find_similar_files
from datetime import datetime


from google.cloud.firestore_v1 import query
import os

from reportlab.platypus.para import Paragraph


# Initialize Flask app
app = Flask(__name__)


# Generate a random secret key
secret_key = os.urandom(24)

# Set the secret key in your Flask app configuration
app.secret_key = secret_key

# Initialize Firebase credentials
cred = credentials.Certificate('') # Provide the path to your service account key JSON file
firebase_admin.initialize_app(cred, {'databaseURL'})

# Create Firestore client
db = firestore.client()

# Define Patient model
class Patient:
    def __init__(self, id, name, admission_date, discharge_date, diagnosis, treatment, doctor, ward, room_number, billing_status, outcome, comments):
        self.id = id
        self.name = name
        self.admission_date = admission_date
        self.discharge_date = discharge_date
        self.diagnosis = diagnosis
        self.treatment = treatment
        self.doctor = doctor
        self.ward = ward
        self.room_number = room_number
        self.billing_status = billing_status
        self.outcome = outcome
        self.comments = comments

# Homepage


@app.route('/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        users_ref = db.collection('users')

        # Retrieve data from the collection
        query = users_ref.get()
        for doc in query:
            # Access the document ID and data
            doc_id = doc.id
            data = doc.to_dict()



        if data['email'] == username and data['password'] == password:
                # Password matches, user is authenticated

            print("Person authenticated")
            return render_template('home_tab.html')

        else:
                # Password does not match, show error message
                print('Incorrect password. Please try again.')


    return render_template('login.html')

@app.route('/home_tab', methods = ['GET', 'POST'])
def home_tab():

    return render_template('home_tab.html')


@app.route('/signup', methods = ['GET', 'POST'])
def signup():

    if request.method == 'POST':
        # Get the data from the request form
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Perform validation on the form data as needed
        if password != confirm_password:
            return 'Password and Confirm Password do not match'

        # Create a new document in the 'users' collection with the form data
        user_data = {
            'username': username,
            'email': email,
            'password': password
        }
        db.collection('users').add(user_data)

        # Redirect to login page after successful sign up
        return redirect(url_for('login'))
    else:
        # Render sign up form for GET requests
        return render_template('signup.html')

@app.route('/patient_options')

def patient_options():

    return render_template('patient_options.html')


@app.route('/patient_add', methods = ['GET', 'POST'])
def patient_add():
    if request.method == "POST":

        username = request.form.get('username')
        name = request.form.get('name')
        admission_date = request.form.get('admission_date')
        discharge_date = request.form.get('discharge_date')
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        doctor = request.form.get('doctor')
        ward = request.form.get('ward')
        room_number = request.form.get('room_number')
        billing_status = request.form.get('billing_status')
        outcome = request.form.get('outcome')
        comments = request.form.get('comments')

        patient_data = {
            'username': username,
            'name': name,
            'admission_date': admission_date,
            'discharge_date': discharge_date,
            'diagnosis': diagnosis,
            'treatment': treatment,
            'doctor': doctor,
            'ward': ward,
            'room_number': room_number,
            'billing_status': billing_status,
            'outcome': outcome,
            'comments': comments
        }

        # Add patient_data to the 'patient' collection
        db.collection('patient').add(patient_data)

        return render_template('home_tab.html')

    else:

        return render_template('patient_add.html')

@app.route('/patient_search', methods=['GET', 'POST'])
def patient_search():
    if request.method == 'POST':
        # Get email from form data
        email = request.form.get('email')

        # Query Firestore for patient with matching email
        patients_ref = db.collection('patient')
        query = patients_ref.where('username', '==', email).get()

        # Initialize an empty list to store patient data
        patients = []

        # Loop through query results and append patient data to list
        for doc in query:
            patients.append(doc.to_dict())

        print(patients)

        if not patients:
            # Render template with error message if no patient found
            error_message = 'No patient found with email: {}'.format(email)
            return render_template('patient_not_found.html', error_message=error_message)

        # Store email data in session
        #session['email'] = email

        # Render template with patient data
        return render_template('patient_search.html', patients=patients)

    # Render the form for GET requests
    return render_template('patient_search.html')

@app.route('/pdf_gen', methods=['GET', 'POST'])
def pdf_gen():
    if request.method == "POST":

        username = request.form.get('username')
        admission_date = request.form.get('admission_date')

        patients_ref = db.collection('patient')
        query = patients_ref.where('username', '==', username).where('admission_date', '==', admission_date).get()
        # Initialize an empty list to store patient data
        patients = []
        #print(query)

        # Loop through query results and append patient data to list
        for doc in query:
            patients.append(doc.to_dict())

        print(patients)

        if not patients:
            # Render template with error message if no patient found
            error_message = 'No patient found with username for the given date: {}'.format(username)
            return render_template('patient_not_found.html', error_message=error_message)

        # Create a filename for the PDF
        filename = f"{username}_{admission_date}"

        # Create a PDF document with landscape orientation
        doc = SimpleDocTemplate(f"{filename}.pdf", pagesize=letter)

        # Define styles for the document
        styles = getSampleStyleSheet()

        # Add the title to the document
        title = Paragraph("MEDICULOUS", styles['h1'])
        subtitle = Paragraph("Medical Report", styles['h2'])
        doc_title = [title, subtitle]
        doc.build(doc_title)

        # Create a list to hold the table data
        table_data = []

        # Add table header
        table_data.append(
            ['Name', 'Admission Date', 'Discharge Date', 'Diagnosis', 'Treatment', 'Doctor', 'Ward', 'Room Number',
             'Billing Status', 'Outcome', 'Comments'])

        # Loop through patient data and append to table data
        for patient in patients:
            table_data.append(
                [patient['name'],
                 patient['admission_date'],
                 patient['discharge_date'],
                 patient['diagnosis'],
                 patient['treatment'],
                 patient['doctor'],
                 patient['ward'],
                 patient['room_number'],
                 patient['billing_status'],
                 patient['outcome'],
                 patient['comments']]
            )

        # Create the table and set its style
        table = Table(table_data, colWidths=[100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100])

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        # Add the table to the PDF document and build it
        doc.build([table])
        # Render template with success message and PDF link
        success_message = 'PDF generated successfully.'
        print(success_message)

        return render_template('report.html', patients = patients)

    return render_template('pdf_gen.html')


@app.route('/quick_consult_search', methods=['GET', 'POST'])
def quick_consult_search():
    if request.method == 'POST':
        directory_path = "Corpus"
        search_string = request.form['search_string']
        threshold = 0.1
        matches = find_similar_files(directory_path, search_string, threshold)
        return render_template('quick_consult_search.html', search_string=search_string, matches=matches)
    return render_template('quick_consult_search.html')





@app.route('/add_appointment', methods = ['GET', 'POST'])
def add_appointment():
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        doctor = request.form.get('doctor')

        # Convert the appointment date and time to a datetime object
        #appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")

        # Check if the doctor has any other appointments at the same date and time
        appointments_ref = db.collection('appointment')
        appointments_query = appointments_ref.where('doctor', '==', doctor).where('appointment_date', '==', appointment_date).where('appointment_time', '==', appointment_time).get()

        if len(appointments_query) > 0:
            # The doctor already has an appointment at the same date and time
            error_message = f"{doctor} already has an appointment at {appointment_date} and {appointment_time}. Please choose a different date or time."
            return render_template('appointment_error.html', error_message=error_message)

        # The appointment slot is available for the selected doctor, so add the appointment to the database
        appointment_data = {
            'patient_email': email,
            'patient_name': name,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'doctor': doctor,
        }

        db.collection('appointment').add(appointment_data)

        return render_template('home_tab.html')

    else:
        return render_template('add_appointment.html')


@app.route('/appointment_option')
def appointment_option():

    return render_template("appointment_option.html")


@app.route('/appointment_search', methods=['GET', 'POST'])
def appointment_search():
    if request.method == "POST":

        doctor = request.form.get('doctor')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')

        appointment_ref = db.collection('appointment')
        query = appointment_ref.where('appointment_date', '==', appointment_date).where('appointment_time', '==',
                                                                                        appointment_time).where(
            'doctor', '==', doctor).get()

        # Initialize an empty list to store patient data
        appointments = []

        # Loop through query results and append patient data to list
        for doc in query:
            appointments.append(doc.to_dict())

        print(appointments)

        if not appointments:
            # Render template with error message if no patient found
            error_message = 'No appointments found for Doctor: {}'.format(doctor)
            return render_template('appointment_not_found.html', error_message=error_message)

        # Store email data in session
        # session['email'] = email

        # Render template with patient data
        return render_template('appointment_search.html', appointments=appointments)

    return render_template("appointment_search.html")


@app.route('/appointment_not_found')
def appointment_not_found():
    return render_template('appointment_not_found.html')

@app.route('/appointment_delete', methods = ['GET', 'POST'])
def appointment_delete():
    if request.method == "POST":

        doctor = request.form.get('doctor')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')

        appointment_ref = db.collection('appointment')
        query = appointment_ref.where('appointment_date', '==', appointment_date).where('appointment_time', '==', appointment_time).where('doctor', '==', doctor).get()

        # Loop through query results and delete matching document
        for doc in query:
            doc.reference.delete()

        # Render template with success message
        success_message = 'Appointment deleted successfully!'
        return render_template('appointment_delete.html', success_message=success_message)

    return render_template("appointment_delete.html")


@app.route('/inventory_option')
def inventory_options():

    return render_template('inventory_options.html')

@app.route('/add_inventory.html', methods = ["GET", "POST"])

def add_inventory():
    if request.method == 'POST':
        # Get input data from form
        product_id = request.form.get('product_id')
        product_name = request.form.get('product_name')
        manufacturer = request.form.get('manufacturer')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        # Check if the same product with same manufacturer exists in inventory
        inventory_ref = db.collection('Inventory')
        query = inventory_ref.where('product_name', '==', product_name).where('manufacturer', '==', manufacturer).get()

        # If product exists in inventory, show error message
        if len(query) > 0:
            error_message = 'Product with name {} and manufacturer {} already exists in inventory. Please update instead.'.format(
                product_name, manufacturer)
            return render_template('add_inventory.html', error_message=error_message)

        # Add new product to inventory
        inventory_ref.add({
            'product_id': product_id,
            'product_name': product_name,
            'manufacturer': manufacturer,
            'quantity': quantity,
            'price': price
        })

        # Show success message
        success_message = 'Product {} added to inventory successfully.'.format(product_name)
        return render_template('add_inventory.html', success_message=success_message)

    return render_template('add_inventory.html')

@app.route('/delete_inventory', methods=["GET", "POST"])
def delete_inventory():
    if request.method == "POST":
        product_id = request.form.get("product_id")


        # Check if product exists in inventory
        inventory_ref = db.collection("Inventory")
        inventory_query = inventory_ref.where("product_id", "==", product_id).get()

        if len(inventory_query) == 0:
            error_message = "Product not found in inventory"
            return render_template("delete_inventory.html", error_message=error_message)

        # Delete product from inventory
        for inventory in inventory_query:
            inventory_ref.document(inventory.id).delete()

        success_message = "Product deleted successfully"
        return render_template("delete_inventory.html", success_message=success_message)

    return render_template("delete_inventory.html")



@app.route('/update_inventory', methods=["GET", "POST"])
def update_inventory():
    if request.method == "POST":
        # Get product_id and quantity from the form
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')

        # Update the quantity in the Firebase database
        inventory_ref = db.collection('Inventory')
        inventory_docs = inventory_ref.where('product_id', '==', product_id).get()

        # Check if the product_id exists in the database
        if len(inventory_docs) == 0:
            return render_template('product_not_found.html', error_message='Product ID does not exist')

        # Update the quantity if the product_id exists
        inventory_doc = inventory_docs[0]
        inventory_doc_ref = inventory_ref.document(inventory_doc.id)
        inventory_doc_ref.update({'quantity': int(quantity)})

        # Render the success message
        success_message = f'Product with ID {product_id} updated successfully'
        return render_template('update_inventory.html', success_message = success_message)

    # Render the update_inventory.html template
    return render_template('update_inventory.html')



@app.route('/inventory_search', methods=["GET", "POST"])
def inventory_search():
    if request.method == "POST":
        product_name = request.form["product_name"]
        inventory_ref = firestore.client().collection('Inventory')
        query = inventory_ref.where("product_name", "==", product_name).get()

        if not query:
            error_message = "Product not found in inventory"
            return render_template("search_inventory.html", error_message=error_message)

        inventory = []
        for document in query:
            inventory.append(document.to_dict())

        return render_template("inventory_search.html", inventory=inventory)

    return render_template("inventory_search.html")


'''
@app.route('/lookup', methods=['GET', 'POST'])
def lookup():
    if request.method == 'POST':
        # Get email data from session
        email = session.get('email')

        if not email:
            # Render error template if email not found in session
            error_message = 'Email not found in session'
            return render_template('patient_not_found.html', error_message=error_message)

        # Query Firestore for patient with matching email
        patients_ref = db.collection('patient')
        query = patients_ref.where('username', '==', email).get()

        # Initialize an empty list to store patient data
        patients = []

        # Loop through query results and append patient data to list
        for doc in query:
            patients.append(doc.to_dict())

        # Render template with patient data
        return render_template('lookup.html', patients=patients)

    # Render the form for GET requests
    return render_template('patient_search.html')
'''
'''
@app.route('/')
def test():
    users_ref = db.collection('users')

    # Retrieve data from the collection
    query = users_ref.get()
    for doc in query:
        # Access the document ID and data
        doc_id = doc.id
        data = doc.to_dict()
        print(data['username'])
'''
# Add Patient



if __name__ == '__main__':
    app.run(debug=True)
