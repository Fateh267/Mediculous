@app.route('/add_patient', methods=['POST'])
def add_patient():
    # Get form data
    id = request.form['id']
    name = request.form['name']
    admission_date = request.form['admission_date']
    discharge_date = request.form['discharge_date']
    diagnosis = request.form['diagnosis']
    treatment = request.form['treatment']
    doctor = request.form['doctor']
    ward = request.form['ward']
    room_number = request.form['room_number']
    billing_status = request.form['billing_status']
    outcome = request.form['outcome']
    comments = request.form['comments']

    # Create patient object
    patient = Patient(id, name, admission_date, discharge_date, diagnosis, treatment, doctor, ward, room_number, billing_status, outcome, comments)

    # Add patient data to Firestore
    db.collection('patients').document(id).set(patient.__dict__)

    return redirect('/')

# Get Patients
@app.route('/get_patients')
def get_patients():
    # Get all patient data from Firestore
    patients = db.collection('patients').get()

    # Create list to store patient objects
    patient_list = []

    # Loop through patient data and create patient objects
    for patient in patients:
        patient_data = patient.to_dict()
        patient_obj = Patient(patient_data['id'], patient_data['name'], patient_data['admission_date'], patient_data['discharge_date'], patient_data['diagnosis'], patient_data['treatment'], patient_data['doctor'], patient_data['ward'], patient_data['room_number'], patient_data['billing_status'], patient_data['outcome'], patient_data['comments'])
        patient_list.append(patient_obj)

    return render_template('patients.html', patients=patient_list)
