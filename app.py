from flask import Flask, render_template, redirect, url_for, Response,request, make_response,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func 
from datetime import datetime,date as dt_date

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my-secret-key'
db = SQLAlchemy(app)


with app.app_context():
     db.create_all()

# ADD THIS LINE HERE:
CATEGORIES = ["Food", "Transport", "Rent", "Utilities"]

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dt_date.today) 
    
def parse_date_or_none(s: str):
    if not s:
        return None
    try: 
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
            return None
    

@app.get("/")
def index():
    # 1 read query string

    start_str = (request.args.get("start") or "").strip()
    end_str = (request.args.get("end") or "").strip()
    selected_category = (request.args.get("category") or "").strip()
    
    # 2 parsing

    start_date = parse_date_or_none(start_str)
    end_date = parse_date_or_none(end_str)
    
    if start_date and end_date and end_date < start_date:
        flash("End date cannot be before start date", "error")
        start_date = end_date = None
        start_str = end_str = ""

    q = Expense. query
    

    if start_date:
        q = q.filter(Expense.date >= start_date)
    if end_date:
        q = q.filter(Expense.date <= end_date)
    if selected_category:  # category filter
        q = q.filter(Expense.category == selected_category)
    
    expenses = q.order_by(Expense.date.desc(), Expense.id.desc()).all()
    total=round(sum(e.amount for e in expenses),2)
    
    #pie chart
    cat_q = db.session.query(Expense.category, func.sum(Expense.amount))

    if start_date:
        cat_q = cat_q.filter(Expense.date > start_date)

    if end_date:
        cat_q = cat_q.filter(Expense.date <= end_date)

    if selected_category:
        cat_q = cat_q.filter(Expense.category == selected_category)

    cat_rows = cat_q.group_by(Expense.category).all()
    print(cat_rows)
    cat_labels = [c for c, _ in cat_rows]
    cat_values = [round(float(s or 0),2) for _, s in cat_rows]


    # day chart

    day_q = db.session.query(Expense.date, func.sum(Expense.amount))

    if start_date:
        day_q = day_q.filter(Expense.date >= start_date)
    if end_date:
        day_q = day_q.filter(Expense.date <= end_date)
    if selected_category:
        day_q = day_q.filter(Expense.category == selected_category)

    day_rows = day_q.group_by(Expense.category).order_by(Expense.date).all()

    #(variable) cat_rows: List[Any]

    day_labels = [d.isoformat() for d, _ in day_rows]
    day_values = [round(float(s or 0),2) for _, s in day_rows]

    
    print(expenses)
    return render_template("index.html", expenses=expenses,
                                         categories=CATEGORIES,
                                         today=dt_date.today().isoformat(),
                                         total=total,
                                         start_str=start_str,
                                         end_str=end_str,
                                         selected_category=selected_category,
                                         cat_labels=cat_labels,
                                         cat_values=cat_values,
                                         day_lables=day_labels,
                                         day_values=day_values)


#@app.route("/add", methods=['POST'])
#def add():
#    print("Form received:", dict(request.form))
#    return make_response("Form received check the console")


@app.route("/add", methods=['POST'])
def add():
    description = (request.form.get("description") or "").strip()
    amount_str = (request.form.get("amount") or "").strip()
    category = (request. form.get("category") or "") .strip()
    date_str = (request. form.get("date") or "").strip()


    if not description or not amount_str or not category:
        flash("Please fill description, amount, and category", "error")
        return redirect(url_for("index"))

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError

    except ValueError:
        flash("Amount must be a positive number", "error")
        return redirect(url_for("index"))    

    try:
        d = datetime. strptime(date_str, "%Y-m-sd") .date() if date_str else date.today()
    except ValueError:
        d = dt_date.today()

        e = Expense(description=description, amount=amount, category=category, date=d)
        db.session.add(e)
        db.session.commit()

        flash("Expense added", "success")
        return redirect(url_for("index"))  




@app. route('/delete/<int:expense_id>' ,methods=['POST' ] )
def delete(expense_id):
    e = Expense.query.get_or_404(expense_id)
    db.session.delete(e)
    db.session.commit()
    flash("Expense deleted", "success")
    return redirect(url_for("index"))  




@app. route('/edit/<int:expense_id>' ,methods=['GET'])
def edit(expense_id):
     e = db.get_or_404(Expense, expense_id)
     return render_template("edit.html", expense=e, categories=CATEGORIES, today=dt_date. today().isoformat())   



@app. route('/edit/<int:expense_id>',methods=['POST' ])
def edit_post(expense_id):
    e = Expense.query.get_or_404(expense_id)

    description = (request.form.get("description") or "").strip()
    amount_str = (request. form.get("amount") or "").strip()
    category = (request. form.get("category") or "").strip()
    date_str = (request. form.get("date") or "").strip()

    print(request.form)     

    if not description or not amount_str or not category:
        flash("Please fill description, amount, and category", "error")
        return redirect(url_for("edit", expense_id=expense_id))

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a positive number", "error")
        return redirect(url_for("edit", expense_id=expense_id))

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else dt_date.today()
    except ValueError:
        d = dt_date. today()

    e.description = description
    e. amount = amount
    e.category = category
    e.date = d

    db.session.commit()
    flash("Expense updated", "success")
    return redirect(url_for("index"))    




@app.route("/export")
def export_csv():
    start_str = (request.args.get("start") or "").strip()
    end_str = (request.args.get("end") or "").strip()
    selected_category = (request.args.get("category") or "").strip()
    
    start_date = parse_date_or_none(start_str)
    end_date = parse_date_or_none(end_str)

    q = Expense.query

    if start_date:
        q = q.filter(Expense.date >= start_date)
    if end_date:
        q = q.filter(Expense.date <= end_date)
    if selected_category:
        q = q.filter(Expense.category == selected_category)

    expenses = q.order_by(Expense.date, Expense.id).all()

    lines = ["date,description,category,amount"]
    for e in expenses:
        # Fixed: whitespace removed from format specifier
        lines.append(f"{e.date.isoformat()},{e.description},{e.category},{e.amount:.2f}")

    csv_data = "\n".join(lines)

    fname_start = start_str or "all"
    fname_end = end_str or "all"
    filename = f"expenses_{fname_start}_to_{fname_end}.csv"

    return Response(csv_data, headers={"Content-Type": "text/csv", "Content-Disposition": f"attachment; filename={filename}"})

if __name__=="__main__":
    app.run(debug=True, port=4848)




