# SQL Alchemy
- **SQL Alchemy** : SQL toolkit and ORM for Python.
- **Alembic** : Database migration tool used to generate and run migration scripts.

_**Session** -> Session is a workspace, scratchpad, and transaction mamager for interacting with the database_

---
### Transaction Functions

| **Function** | **What it does** |
|--------------|------------------|
|`session.add()`|Places a python model into session's statging area                  |
|`session.flush()`| Send all pending SQL statements to database but doesnot commit the transaction
|`session.commit()`|Finalizes the current transaction permanently writing all flushed changes into database
|`session.rollback()`|Aborts the current transaction and reverts all uncommitted changed made during the session|

---

## Managing Transactions & Race Conditions

### How Transactions Work

Every time you interact with a session, SQLAlchemy automatically opens a database transaction (or you can manage them explicitly with `with session.begin():`). Transactions ensure **ACID** compliance: either all operations succeed together, or none of them do.

### Handling Race Conditions (Concurrency Control)

When multiple users or microservices try to modify the same database row simultaneously, **race conditions** occur (e.g., two requests reading balance as $100, both subtracting $50, and overwriting each other). SQLAlchemy provides two main strategies to handle this:

#### A. Pessimistic Locking (Database-level locks)

You lock the rows at the database level during the query so other transactions cannot modify them until yours completes.

```python
# Issues a 'SELECT ... FOR UPDATE' query, locking the row
stmt = select(User).filter_by(id=1).with_for_update()
user = (await session.execute(stmt)).scalar_one()
user.balance -= 50
await session.commit()

```

#### B. Optimistic Locking (Version tracking)

Instead of locking rows (which can hurt performance), you add a version column. If another transaction modifies the row first, your update fails because the version number has changed.

```python
from sqlalchemy import Column, Integer, String


class Account(Base):
  __tablename__ = "accounts"
  id = Column(Integer, primary_key=True)
  balance = Column(Integer)
  version = Column(Integer, nullable=False)

  # Tell SQLAlchemy to use this column for version tracking
  __mapper_args__ = {"version_id_col": version}

```

---

## 3. SQLAlchemy Query Functions (Modern 2.0 Style)

Modern SQLAlchemy uses the Core `select()` construct combined with session execution methods.

| Function / Method | Purpose | Example | Return Type |
| --- | --- | --- | --- |
| **`select(Model)`** | Constructs a SQL `SELECT` statement. Base builder for all queries. | `stmt = select(User).where(User.name == "Alice")` | `Select` object |
| **`session.execute(stmt)`** | Executes the statement against the database engine. | `result = await session.execute(stmt)` | `Result` object |
| **`.scalars()`** | Strips away metadata rows/columns, returning raw model instances instead of row tuples. | `users = result.scalars().all()` | `ScalarResult` |
| **`.scalar_one()`** | Fetches exactly one result. Raises an error if 0 or more than 1 row matches. | `user = result.scalar_one()` | Model instance |
| **`.scalar_one_or_none()`** | Fetches one result, or returns `None` if no rows match. | `user = result.scalar_one_or_none()` | Model instance or `None` |
| **`.all()`** | Fetches all rows matching the query into a Python list. | `all_users = result.scalars().all()` | `List[Model]` |
| **`.first()`** | Fetches the first row from the result set, or `None`. | `first_user = result.scalars().first()` | Model instance or `None` |
| **`.filter_by(**kwargs)`** | Quick keyword-argument filtering (equality check only). | `select(User).filter_by(status="active")` | `Select` object |
| **`.where(*criteria)`** | Advanced filtering using Python comparison operators (`==`, `>`, `in_()`). | `select(User).where(User.age >= 18)` | `Select` object |
| **`.join(Target)`** | Performs an INNER JOIN with a related model table. | `select(User).join(User.posts)` | `Select` object |


