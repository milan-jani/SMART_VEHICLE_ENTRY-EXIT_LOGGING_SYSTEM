from flask import Flask, render_template, request
import app.csv_utils as csv_utils

app = Flask(__name__)
plate_number = ""

@app.route("/", methods=["GET", "POST"])
def visitor_form():
    global plate_number
    success_message = None  # message to pass to template
    if request.method == "POST":
        vehicle = request.form["vehicle"]
        name = request.form["name"]
        phone = request.form["phone"]
        purpose = request.form["purpose"]

        # update using vehicle number from form
        csv_utils.update_visitor_details_for_last(vehicle, name, phone, purpose)

        success_message = "✅ Visitor logged successfully!"

    return render_template("form.html", plate=plate_number, success_message=success_message)
