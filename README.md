# UoB Voting App 

Beta Version of the voting app for UoB Student Council Elections 2024, made in Flask. 

## Directory/Data

**student_data.csv** = Student Data with ID, Name & Course, shared by UoB  
**voters.csv** = Registered voters  
**nominees.csv** = Candidates running for election with their respective position & vote count

## How to run


### 1. Change email address in app/auth/routes.py lines (256) & (274), and app/register/routes.py line (12):
```
sender_address = "domain@gmail.com" 
```
### 2. Set app password on Google:
Visit [this link](https://accounts.google.com/v3/signin/identifier?continue=https%3A%2F%2Fmyaccount.google.com%2Fapppasswords&followup=https%3A%2F%2Fmyaccount.google.com%2Fapppasswords&ifkv=ASKXGp0mvda2mUS-4Iuq-oDCKDcqVEnbEjmFCNtztqKCJEOzwiC8zJQC6L1UTsauBa8d1T2HFUBu5A&osid=1&passive=1209600&rart=ANgoxcctWpClpk-e1e82lr36OXRpFS3yNTPoIQeGw7Gx1E_m8sTNMKNtUfkrYmm0REjRyYB_NygDdRaj6jyfNM_F_IDCclLfdg&service=accountsettings&flowName=GlifWebSignIn&flowEntry=ServiceLogin&dsh=S-32962069%3A1706579171935790&theme=glif) & generate an app name and password for sending confirmation codes via email

### 3. Store environment variables:

```
touch .env
```

### 4. Download requirements:

```
pip install -r requirements.txt
```

### 4. Run the app:

```
python run.py
```

### 6. Access the app:
- Go to `http://127.0.0.1:5000/` to access the app.

