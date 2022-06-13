import re
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, render_template, request
from flask.globals import session

# Global variable to access dynamo DB tables and resources
dynamoDb = boto3.resource("dynamodb")

# Global variables to access employee table collection in dynamoDB
employee_collection = dynamoDb.Table("employee")

# Global variables to access products table collection in DynamoDB
product_collection = dynamoDb.Table("Products")

# Global variables to access location table collection in DynamoDB
location_collection = dynamoDb.Table("location")

# Global variables to access transfer table collection in DynamoDB
transfer_collection = dynamoDb.Table("Transfer")

# Global variables to access report table collection in DynamoDB
report_collection = dynamoDb.Table("Report")

app = Flask(__name__)

# setting secret key to access session variables across the application
app.secret_key = "xyz"


@app.route("/")
def root():
    return render_template("login.html")


@app.route("/authentication", methods=["POST"])
def login():
    if request.method == "POST":
        user_email = request.form["user_email"]
        user_password = request.form["password"]
        check = check_user_authentication(user_email, user_password)
        if check:
            return render_template("home.html", session=session)
        else:
            message = "Invalid Email  Or Password. Please Try Again."
            return render_template("login.html", message=message)


# Function to check the authentication of the employee
def check_user_authentication(user_email, user_password):
    employee_details = employee_collection.scan()
    for employee_detail in employee_details["Items"]:
        if employee_detail["employee_email"].upper() == user_email.upper():
            if employee_detail["password"] == user_password:
                if employee_detail["employee_status"] == "ACTIVE":
                    session["employee_name"] = employee_detail["employee_name"]
                    return True

    return False


@app.route("/home")
def home():
    return render_template("home.html", session=session)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/product")
def product():
    return render_template(
        "product.html", products=get_product_details(), session=session
    )


def get_product_details():
    product_details = product_collection.scan()
    return product_details


@app.route("/location")
def location():
    return render_template(
        "location.html", locations=get_location_details(), session=session
    )


def get_location_details():
    location_details = location_collection.scan()
    return location_details


@app.route("/transfer")
def transfer():
    return render_template(
        "transfer.html", transfers=get_transfer_details(), session=session
    )


def get_transfer_details():
    transfer_details = transfer_collection.scan()
    return transfer_details


@app.route("/report")
def report():
    return render_template(
        "report.html",
        reports=get_report_details(),
        session=session,
        locations=get_location_details(),
    )


@app.route("/viewProduct")
def view_product():
    return render_template("viewProduct.html")


@app.route("/editProduct")
def edit_product():
    return render_template("editProduct.html")


@app.route("/editLocation")
def edit_location():
    return render_template("editLocation.html")


@app.route("/transferProduct")
def transfer_product():
    return render_template(
        "transferProduct.html",
        locations=get_location_details(),
        products=get_product_details(),
    )


@app.route("/addProduct")
def add_product():
    return render_template(
        "addProduct.html",
        locations=get_location_details(),
        img_path="/static/add_image.png",
    )


@app.route("/addLocation")
def add_location():
    return render_template("addLocation.html")


@app.route("/registerAuthentication", methods=["POST"])
def check_register():
    if request.method == "POST":
        employee_name = request.form["employee_name"]
        employee_email = request.form["employee_email"]
        password = request.form["password"]
        regex = "^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$"
        employee_details = employee_collection.scan()
        for employee_detail in employee_details["Items"]:
            if employee_detail["employee_email"].upper() == employee_email.upper():
                message = "Entered Email Already Exists"
                return render_template("register.html", message=message)

        if re.search(regex, employee_email):
            employee_collection.put_item(
                Item={
                    "employee_id": str(uuid.uuid1()),
                    "employee_name": employee_name,
                    "employee_email": employee_email,
                    "employee_status": "ACTIVE",
                    "password": password,
                }
            )
            message = "Registration Successful. Please LogIn to Continue."
            return render_template("login.html", message=message)
        else:
            message = "Invalid Email format. Try Again"
            return render_template("register.html", message=message)


@app.route("/addNewLocation", methods=["POST"])
def add_new_location():
    if request.method == "POST":
        location_name = request.form["location_name"]
        location_address = request.form["location_address"]
        location_details = location_collection.scan()
        for location_detail in location_details["Items"]:
            if (
                location_detail["location_name"].upper() == location_name.upper()
                and location_detail["location_address"].upper()
                == location_address.upper()
            ):
                message = "Location Name or Address already exists"
                return render_template("addLocation.html", message=message)

        location_collection.put_item(
            Item={
                "location_id": str(uuid.uuid1()),
                "location_name": location_name,
                "location_address": location_address,
            }
        )
        return render_template("location.html", locations=get_location_details())


@app.route("/addNewProduct", methods=["POST"])
def add_new_product():
    if request.method == "POST":
        product_name = request.form["product_name"]
        product_description = request.form["product_description"]
        product_category = request.form["product_category"]
        img_url = str(request.files.get("image_uploaded"))
        print(img_url)
        product_details = product_collection.scan()
        for product_detail in product_details["Items"]:
            if product_detail["product_name"].upper() == product_name.upper():
                message = "Product with Same name and details already exists \n Click on Edit Product to update Product Details"
                return render_template(
                    "addProduct.html",
                    message=message,
                    locations=get_location_details(),
                    img_path="/static/add_image.png",
                )
        if img_url == "":
            product_img_url = "https://bucket3775816.s3.amazonaws.com/add_image.png"
        else:
            path = "C:\\Users\\91855\\Downloads\\"
            split_img = img_url.split("'")
            print("si" + split_img)
            path = path + split_img[1].replace("'", "")
            product_img_url = upload_img_s3(path, split_img[1].replace("'", ""))

        product_collection.put_item(
            Item={
                "product_id": str(uuid.uuid1()),
                "product_name": product_name,
                "product_description": product_description,
                "product_category": product_category,
                "product_image_url": product_img_url,
            }
        )
        return render_template("product.html", products=get_product_details())


def upload_img_s3(image_path, image_name):
    s3 = boto3.resource(service_name="s3")
    s3_client = boto3.client("s3")
    s3.meta.client.upload_file(
        Filename=image_path, Bucket="bucket3775816", Key=image_name
    )
    url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": "bucket3775816", "Key": image_name},
    )
    url = url.split("?")
    return url[0]


@app.route("/addProductStock/<product_name>")
def add_product_stock(product_name):
    product = product_name
    return render_template(
        "addStock.html",
        productName=product,
        session=session,
        locations=get_location_details(),
    )


@app.route("/addStock", methods=["POST"])
def add_Stock():
    if request.method == "POST":
        product_name = request.form["product_name"]
        product_location = request.form["product_location"]
        product_quantity = request.form["product_quantity"]
        check = checkLocation(product_location)
        if check and int(product_quantity) > 0:
            response = report_collection.query(
                KeyConditionExpression=Key("product_location").eq(product_location)
                & Key("product_name").eq(product_name)
            )
            if len(response["Items"]) == 0:
                print("Lenght of response in addstock" + str(len(response["Items"])))
                report_collection.put_item(
                    Item={
                        "product_name": product_name,
                        "product_location": product_location,
                        "product_quantity": product_quantity,
                    }
                )
                return render_template(
                    "report.html",
                    reports=get_report_details(),
                    locations=get_location_details,
                    session=session,
                )
            elif len(response["Items"]) > 0:
                print("Lenght of response in addstock" + str(len(response["Items"])))
                original_quantity = ""
                for item in response["Items"]:
                    original_quantity = item["product_quantity"]

                report_collection.update_item(
                    Key={
                        "product_name": product_name,
                        "product_location": product_location,
                    },
                    UpdateExpression="set product_quantity=:q",
                    ExpressionAttributeValues={
                        ":q": int(original_quantity) + int(product_quantity)
                    },
                )
                return render_template(
                    "report.html",
                    reports=get_report_details(),
                    session=session,
                    locations=get_location_details(),
                )
        else:
            message = "Product Quantity or Product Location is Invalid"
            return render_template(
                "addStock.html",
                productName=product_name,
                session=session,
                locations=get_location_details(),
                message=message,
            )


def get_report_details():
    report_details = report_collection.scan()
    return report_details


def checkLocation(product_location):
    location_details = location_collection.scan()
    for location_detail in location_details["Items"]:
        if location_detail["location_name"].upper() == product_location.upper():
            return True

    return False


@app.route("/deleteProductStock/<product_name>")
def delete_product_stock(product_name):
    product = product_name
    return render_template(
        "deleteStock.html",
        productName=product,
        session=session,
        locations=get_location_details(),
    )


@app.route("/deleteStock", methods=["POST"])
def delete_Stock():
    if request.method == "POST":
        product_name = request.form["product_name"]
        product_location = request.form["product_location"]
        product_quantity = request.form["product_quantity"]
        check = checkLocation(product_location)
        if check and int(product_quantity) > 0:
            response = report_collection.query(
                KeyConditionExpression=Key("product_location").eq(product_location)
                & Key("product_name").eq(product_name)
            )
            if len(response["Items"]) == 0:
                message = "Invalid Product and Location details to delete Stock"
                return render_template(
                    "deleteStock.html",
                    productName=product_name,
                    session=session,
                    locations=get_location_details(),
                    message=message,
                )
            elif len(response["Items"]) > 0:
                original_quantity = ""
                for item in response["Items"]:
                    original_quantity = item["product_quantity"]

                if int(original_quantity) >= int(product_quantity):
                    report_collection.update_item(
                        Key={
                            "product_name": product_name,
                            "product_location": product_location,
                        },
                        UpdateExpression="set product_quantity=:q",
                        ExpressionAttributeValues={
                            ":q": int(original_quantity) - int(product_quantity)
                        },
                    )
                    return render_template(
                        "report.html",
                        reports=get_report_details(),
                        session=session,
                        locations=get_location_details(),
                    )
                else:
                    message = "Quantity entered is more than product stock"
                    return render_template(
                        "deleteStock.html",
                        productName=product_name,
                        session=session,
                        locations=get_location_details(),
                        message=message,
                    )

        else:
            message = "Product Quantity or Product Location is Invalid"
            return render_template(
                "deleteStock.html",
                productName=product_name,
                session=session,
                locations=get_location_details(),
                message=message,
            )


@app.route("/viewProduct/<product_name>")
def view_product(product_name):
    product = product_name
    return render_template(
        "viewProduct.html",
        productName=product,
        session=session,
        locations=get_location_details(),
    )


@app.route("/transferProductCheck", methods=["POST"])
def transfer_product_check():
    if request.method == "POST":
        from_location = request.form["from"]
        to_location = request.form["to"]
        product_quantity = request.form["quantity"]
        product_name = request.form["product"]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
