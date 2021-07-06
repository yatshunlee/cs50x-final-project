'''
Lee Yat Shun Jasper's CS50x Final Project
Project Title: Make Your Own Online Shop!!
github id: yatshunlee
email: yatshunlee@gmail.com
'''

import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import time
import datetime

from helpers import login_required, currenttime, list_to_string, string_to_list

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///shop.db")

# .html
@app.route('/', methods=["GET"])
def welcome():
    return render_template("welcome.html")

# done
@app.route("/products", methods=["GET", "POST"])
def products():
    rows = db.execute("SELECT * from products")
    names = []
    prices = []
    for i in range(len(rows)):
        names.append(rows[i]['name'])
        prices.append(rows[i]['price'])

    if request.method == "POST":
        # return from modal
        if request.form.get("return")=="return":
            return render_template("products.html", names=names, prices=prices)

        if len(session) == 0:
            error = "You need an account to like/add to cart."
            return render_template("products.html", names=names, prices=prices, error=error)

        # add to cart
        elif request.form.get("add")=="add":
            user_id = session["user_id"]
            product_id = request.form.get("productid")

            if int(request.form.get("count")) < 1:
                error = "Error: The quantity should be greater than 0."
                return render_template("products.html", names=names, prices=prices, error=error)
            count = request.form.get("count")

            if request.form.get("size") == "NA":
                error = "Error: Size of the product must be chosen."
                return render_template("products.html", names=names, prices=prices, error=error)
            product_size = request.form.get("size")

            db.execute("INSERT INTO cart (user_id, product_id, count, product_size) VALUES(?, ?, ?, ?)", user_id, product_id, count, product_size)
            added = "cart"
            return render_template("products.html", names=names, prices=prices, added=added)

        # add to wishlist
        elif request.form.get("like"):
            product_id = request.form.get("like")
            existedWish = db.execute("SELECT COUNT(*) FROM wish WHERE user_id = :user_id AND product_id = :product_id", user_id=session["user_id"], product_id=product_id)
            if existedWish[0]['COUNT(*)'] != 0:
                error = "Error: You have already liked the product."
                return render_template("products.html", names=names, prices=prices, error=error)
            db.execute("INSERT INTO wish (user_id, product_id) VALUES(?, ?)", session["user_id"], product_id)
            added = "wishlist"
            return render_template("products.html", names=names, prices=prices, added=added)
    # render
    else:
        return render_template("products.html", names=names, prices=prices)

# delete function
@app.route("/productsEdit", methods=["GET", "POST"])
@login_required # ch admin
def productsEdit():
    rows = db.execute("SELECT * from products")
    names = []
    prices = []
    for i in range(len(rows)):
        names.append(rows[i]['name'])
        prices.append(rows[i]['price'])
    if request.method == "POST":
        if request.form.get("edit"):
            price = "price" + str(request.form.get("edit"))
            if not request.form.get(price):
                return render_template("productsedit.html", names=names, prices=prices, error=True)
            newPrice = request.form.get(price)
            product_id = request.form.get("edit")
            db.execute("UPDATE products SET price=:price WHERE id=:product_id", price=newPrice, product_id=product_id)
            return redirect("/productsEdit")
        # elif request.form.get("deleted"):
        #     return render_template("productsedit.html", names=names, prices=prices, deleted=True)
    else:
        return render_template("productsedit.html", names=names, prices=prices)

# front end demo: a msg instead of apology???
@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        # handling empty form.
        if not request.form.get("email"):
            return render_template("contact.html",error="must provide email.")
        if not request.form.get("message"):
            return render_template("contact.html",error="cannot submit a empty message.")
        email = request.form.get("email")
        message = request.form.get("message")
        db.execute("INSERT INTO contact (email, content) VALUES(?, ?)", email, message)
        return redirect("/contact")
    else:
        return render_template("contact.html")

# done
@app.route("/contacted", methods=["GET","POST"])
@login_required # ch admin
def contacted():
    if request.method == "POST":
        id = request.form.get("replyed")
        db.execute("UPDATE contact SET replyed=1 WHERE id = ?", id)
        return redirect("/contacted")
    else:
        rows = db.execute("SELECT * FROM contact")
        return render_template("contacted.html", rows=rows)

# lack of payment (shd be done)
@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    rows = db.execute("SELECT c.cart_id, p.name, p.price, c.count, c.product_size, p.id FROM products AS p JOIN cart AS c ON p.id = c.product_id WHERE c.user_id=:user_id AND c.paid=0",\
      user_id=session["user_id"])
    total = 0
    cart_ids=[]

    for row in rows:
        # displaying photo dynamically
        img = "static/products/"+str(row["id"])+".jpg"
        row["img"] = img

        # counting total price of each row of products
        tmp_total = row["price"]*row["count"]
        total += tmp_total

        # creating list of cart_ids
        cart_ids.append(str(row["cart_id"]))

    cart_ids = list_to_string(cart_ids)

    if request.method == "POST":
        # purchase and update db and photo
        if request.form.get("purchase")=="purchase":
            firstname = request.form.get("firstname")
            surname = request.form.get("surname")
            contact = request.form.get("contact")
            delivery = request.form.get("delivery_method")
            address = request.form.get("address")
            payment = request.form.get("payment_method")

            # error messages
            if total == 0:
                error = "Error: You need to add at least 1 item to the cart."
                return render_template("cart.html", rows=rows, total=total, error=error)
            if (not firstname) or (not surname) or (not contact) or (not address) or (payment == "PMNA") or (delivery == "DMNA"):
                error = "Error: You need to fill in all the information."
                return render_template("cart.html", rows=rows, total=total, error=error)

            # create the transaction date and the invoice number
            date = currenttime()
            db.execute("INSERT INTO invoiceNumber (invoice_date) VALUES (?)", date)
            invoice_number = db.execute("SELECT MAX(invoice_number) FROM invoiceNumber")
            invoice_number = invoice_number[0]['MAX(invoice_number)']
            status = "Checking"

            db.execute("INSERT INTO orders (invoice_id, cart_id, firstname, surname, contact, dm, address, pm, status, total, user_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",\
              invoice_number, cart_ids, firstname, surname, contact, delivery, address, payment, status, total, session["user_id"])
            db.execute("UPDATE cart SET paid=:paid WHERE user_id=:user_id AND paid=0", paid=1, user_id=session["user_id"])
            return redirect("/history")

        # remove item from the list
        else:
            cart_id = request.form.get("remove")
            db.execute("DELETE FROM cart WHERE cart_id = :cart_id",cart_id=cart_id)
            return redirect("/cart")
    else:
        return render_template("cart.html", rows=rows, total=total)

# done
@app.route("/orders", methods=["GET", "POST"])
@login_required # ch admin
def orders():
    if request.method == "POST":
        if request.form.get("invoice_id"):
            invoice = db.execute("SELECT dm, address, cart_id, invoice_id FROM orders WHERE invoice_id=:invoice_id",invoice_id=request.form.get("invoice_id"))
            invoice = invoice[0]

            cart_ids = string_to_list(invoice["cart_id"])
            cart = db.execute("SELECT p.name, c.count, c.product_size FROM cart AS c JOIN products AS p ON c.product_id=p.id WHERE cart_id IN (:cart_ids)",cart_ids=cart_ids)

            return render_template("order.html", invoice=invoice, cart=cart)

        elif request.form.get("delivered"):
            db.execute("UPDATE orders SET status=:status WHERE invoice_id=:invoice_id", status="Delivered", invoice_id=request.form.get("delivered"))
            return redirect("/orders")
    else:
        rows = db.execute("SELECT invoice_date, invoice_id, contact, total, status, firstname, surname, pm FROM orders AS o JOIN invoiceNumber AS i ON o.invoice_id=i.invoice_number")
        return render_template("orders.html", rows=rows)

# done
@app.route("/wish", methods=["GET", "POST"])
@login_required
def wish():
    # for showing information
    rows = db.execute("SELECT p.id, p.name, p.price FROM products AS p JOIN wish AS w ON p.id = w.product_id WHERE w.user_id=:user_id", user_id=session["user_id"])
    for row in rows:
        img = "static/products/"+str(row["id"])+".jpg"
        row["img"] = img

    if request.method == "POST":
        if request.form.get("remove"):
            product_id = request.form.get("remove")
            db.execute("DELETE FROM wish WHERE product_id = :product_id AND user_id = :user_id", product_id=product_id, user_id=session["user_id"])

            # for rendering
            msg = "Removed the selected item."
            rows = db.execute("SELECT p.id, p.name, p.price FROM products AS p JOIN wish AS w ON p.id = w.product_id WHERE w.user_id=:user_id", user_id=session["user_id"])
            for row in rows:
                img = "static/products/"+str(row["id"])+".jpg"
                row["img"] = img
            return redirect("/wish")

        if request.form.get("cart"):
            product_id = request.form.get("cart")
            product_size = request.form.get("size")
            count = int(request.form.get("count"))
            user_id = session["user_id"]
            if (product_size == "NA") or (count < 1):
                error = "Error: The quantity should be greater than 0 or the size must be chosen."
                return render_template("wish.html", rows=rows, msg=error)

            # update db
            db.execute("INSERT INTO cart (user_id, product_id, count, product_size) VALUES(?, ?, ?, ?)", user_id, product_id, count, product_size)
            db.execute("DELETE FROM wish WHERE product_id = :product_id AND user_id = :user_id", product_id=product_id, user_id=session["user_id"])

            # for rendering
            added = "Added to cart."
            rows = db.execute("SELECT p.id, p.name, p.price FROM products AS p JOIN wish AS w ON p.id = w.product_id WHERE w.user_id=:user_id", user_id=session["user_id"])
            for row in rows:
                img = "static/products/"+str(row["id"])+".jpg"
                row["img"] = img
            return render_template("wish.html", rows=rows, msg=added)
    else:
        return render_template("wish.html", rows=rows)

# many
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        if request.form.get("invoice_id"):
            invoice = db.execute("SELECT firstname, surname, contact, dm, address, cart_id, invoice_id FROM orders WHERE invoice_id=:invoice_id",invoice_id=request.form.get("invoice_id"))
            invoice = invoice[0]

            cart_ids = string_to_list(invoice["cart_id"])
            cart = db.execute("SELECT p.name, c.count, c.product_size FROM cart AS c JOIN products AS p ON c.product_id=p.id WHERE cart_id IN (:cart_ids)",cart_ids=cart_ids)

            return render_template("history.html", invoice=invoice, cart=cart)
    else:
        rows = db.execute("SELECT invoice_date, invoice_id, total, status, pm FROM orders AS o JOIN invoiceNumber AS i ON o.invoice_id=i.invoice_number WHERE user_id=:user_id", user_id=session["user_id"])
        return render_template("historys.html", rows=rows)

# done
@app.route("/changepw", methods=["GET", "POST"])
@login_required # ch admin
def changepw():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        user = db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])

        # Ensure current password was submitted
        if not request.form.get("password"):
            return render_template("changepw.html", error="must provide current password")
            # return apology("must provide current password", 403)

        # Ensure new password was submitted
        if not request.form.get("new"):
            return render_template("changepw.html", error="must provide new password")
            # return apology("must provide new password", 403)

        # check current pw
        if not check_password_hash(user[0]["hash"], request.form.get("password")):
            return render_template("changepw.html", error="invalid password")
            # return apology("invalid password", 403)

        # check current pw and new pw
        if (request.form.get("new") == request.form.get("password")):
            return render_template("changepw.html", error="You cannot submit the same password")
            # return apology("You cannot submit the same password", 403)

        # Insert new pw to db
        hash = generate_password_hash(request.form.get("new"))
        db.execute("UPDATE users SET hash=:hash WHERE id=:id", hash=hash, id=session["user_id"])

        # Registered and loged into the mainpage ("/")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepw.html")

# done
@app.route('/login', methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error="must provide username")
            # return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="must provide password")
            # return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error="invalid username and/or password")
            # return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        if rows[0]["isAdmin"] == 1:
            session["Admin"] = True

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# done
@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# done
@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id & pw
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        existedUsers = db.execute("SELECT username FROM users WHERE username = :username", username=request.form.get("username"))

        if not request.form.get("username"):
            error = "Error: Must provide username"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Error: Must provide password"
            return render_template("register.html", error=error)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            error = "Error: Must provide confirmation password"
            return render_template("register.html", error=error)

        # Ensure it's the only username
        elif existedUsers:
            error = "Error: The username is used already. Try a new one."
            return render_template("register.html", error=error)

        elif (request.form.get("confirmation") != request.form.get("password")):
            error = "Error: The confirmation password must be equal to password"
            return render_template("register.html", error=error)

        # Insert information to db
        username = request.form.get("username")
        contact = request.form.get("contact")
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")
        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        # Log in automatically after registered
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Registered and loged into the mainpage ("/")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

