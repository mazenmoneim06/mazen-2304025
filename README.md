# DB Lab 2 - Login & To-Do Application

## 1. Team
| Name | ID | Did what |
|------|----|----------|
| Mazen <abdelmoniem> | <2304025> | Everything (database, back end, front end, README) |

## 2. Technology
- Back end: Python 3 + Flask (Flask sessions, bcrypt, PyMySQL with `%s` placeholders, no ORM)
- Front end: Jinja templates, plain HTML/CSS/JavaScript (responsive, flexbox + media query)
- Database: MySQL, database `registration`

## 3. How to run
1. Install Python 3.10+ and MySQL.
2. Build the database: `mysql -u root -p < database/schema.sql`
3. Copy `.env.example` to `.env` and put your MySQL password and a session secret.
4. Install the libraries: `pip install -r requirements.txt`
5. Start the server: `python app.py`
6. Open http://localhost:3000

## 4. Features
R1 register (+ "Email Already Exists", auto login) · R2 login/logout with the same error message · R3 private list, newest first ·
R4 add · R5 edit · R6 done/not done · R7 delete with confirmation · R8 validation in browser and on server with the exact messages ·
R9 bcrypt hashes, only the given queries with parameters, user_id from the session · R10 responsive, consistent UI with empty state.
Bonus: count of open to-dos.

## 5. Screenshots
See the `screenshots/` folder: register with errors, login, list with some to-dos (one done), phone-sized window.

## 6. Answers
**(a)** `AND user_id = ?` makes sure a user can only change or delete their own to-dos. The to-do id comes from the browser, so anybody can send another user's id. Without it, any logged-in user could edit or delete anybody's to-dos; with it, the statement changes zero rows when the to-do is not theirs.

**(b)** MySQL rejects the insert with a foreign key error (1452), because there is no matching row in `users`. This is **referential integrity** (foreign key constraint).

**(c)** If the database leaks, plain passwords would be exposed. A bcrypt hash is one-way, salted (equal passwords give different hashes) and slow on purpose, so passwords can't be easily recovered; at login we compare the typed password with the hash.

**(d)** `NOT NULL` only forbids NULL. An empty text `''` (or spaces) is a value, so MySQL accepts it. Only our own checks in the browser and on the server can refuse an empty name.
