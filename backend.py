# backend.py
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime, os

Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    category = Column(String(100), default="Uncategorized")
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "amount": self.amount,
            "created_at": self.created_at.isoformat()
        }

def create_app(db_path="budget.db"):
    app = Flask(__name__)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    @app.route("/api/expenses", methods=["GET"])
    def get_expenses():
        session = SessionLocal()
        expenses = session.query(Expense).order_by(Expense.created_at.desc()).all()
        session.close()
        return jsonify([e.to_dict() for e in expenses])

    @app.route("/api/expenses", methods=["POST"])
    def add_expense():
        data = request.json
        if not data or "description" not in data or "amount" not in data:
            return jsonify({"error": "description and amount required"}), 400
        exp = Expense(description=data["description"],
                      category=data.get("category", "Uncategorized"),
                      amount=float(data["amount"]))
        session = SessionLocal()
        session.add(exp)
        session.commit()
        session.refresh(exp)
        session.close()
        return jsonify(exp.to_dict()), 201

    @app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
    def delete_expense(expense_id):
        session = SessionLocal()
        exp = session.get(Expense, expense_id)
        if not exp:
            session.close()
            return jsonify({"error": "not found"}), 404
        session.delete(exp)
        session.commit()
        session.close()
        return jsonify({"status": "deleted"})

    return app
