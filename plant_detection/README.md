# TogetherSO - Plant Disease Detection Platform

TogetherSO is an AI-powered platform designed to help farmers detect plant diseases early and protect their crops. The application uses deep learning models to analyze leaf images and provide actionable recommendations for disease prevention and treatment.

---

## **Table of Contents**
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running the Application](#running-the-application)
4. [Database Setup](#database-setup)
5. [AI Model Integration](#ai-model-integration)
6. [Deployment Instructions](#deployment-instructions)
7. [Contributing](#contributing)
8. [License](#license)

---

## **Prerequisites**

Before running the application, ensure you have the following installed on your system:
- **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/).
- **Django 5.x**: Ensure compatibility with the latest version.
- **PyTorch**: For the AI model.
- **Pillow**: For image processing.
- **MySQL or PostgreSQL**: For database storage.
- **Git**: To clone the repository.
- **Virtual Environment**: Recommended for isolating dependencies.

---

## **Installation**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo-url/togetherso.git
   cd togetherso
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   If using MySQL:
   ```bash
   pip install mysqlclient
   ```

   If using PostgreSQL:
   ```bash
   pip install psycopg2-binary
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root directory:
   ```plaintext
   DJANGO_SECRET_KEY=your_secret_key
   DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1
   DJANGO_DATABASE_URL=postgres://username:password@localhost:5432/togetherso
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_STORAGE_BUCKET_NAME=your_s3_bucket_name
   DJANGO_EMAIL_USER=your_email@gmail.com
   DJANGO_EMAIL_PASSWORD=your_email_password
   ```

   Install `python-decouple` to load environment variables:
   ```bash
   pip install python-decouple
   ```

---

## **Running the Application**

1. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Collect Static Files** (if using production settings):
   ```bash
   python manage.py collectstatic
   ```

3. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```

   Access the app at [http://127.0.0.1:8000](http://127.0.0.1:8000).

4. **Test the AI Engine**:
   - Navigate to the detection page.
   - Upload an image of a plant leaf.
   - The AI engine will analyze the image and display the predicted disease along with prevention steps.

---

## **Database Setup**

TogetherSO supports both **MySQL** and **PostgreSQL**. Below are instructions for setting up each:

### **Using PostgreSQL**
1. Install PostgreSQL:
   - macOS: `brew install postgresql`
   - Ubuntu: `sudo apt install postgresql`
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/).

2. Create a Database and User:
   ```sql
   CREATE DATABASE togetherso;
   CREATE USER togetherso_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE togetherso TO togetherso_user;
   ```

3. Update `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'togetherso',
           'USER': 'togetherso_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### **Using MySQL**
1. Install MySQL:
   - macOS: `brew install mysql`
   - Ubuntu: `sudo apt install mysql-server`
   - Windows: Download from [mysql.com](https://dev.mysql.com/downloads/mysql/).

2. Create a Database and User:
   ```sql
   CREATE DATABASE togetherso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'togetherso_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON togetherso.* TO 'togetherso_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. Update `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'togetherso',
           'USER': 'togetherso_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

---

## **AI Model Integration**

1. **Load the Pre-trained Model**:
   - Place the pre-trained PyTorch model (`plant_disease_model_1_latest.pt`) in the project's root directory.
   - Ensure the `CNN.py` file is correctly configured.

2. **Run Single Predictions**:
   Use the `single_prediction` function in `views.py` to test the AI model:
   ```python
   def single_prediction(image_path):
       image = Image.open(image_path)
       image = image.resize((224, 224))
       input_data = TF.to_tensor(image)
       input_data = input_data.view((-1, 3, 224, 224))
       output = model(input_data)
       output = output.detach().numpy()
       index = np.argmax(output)
       return index
   ```

3. **Verify Disease Information**:
   - Ensure the `disease_info.csv` file is present in the project directory.
   - Load the CSV into the `transform_index_to_disease` dictionary:
     ```python
     data = pd.read_csv('disease_info.csv', encoding='utf-8')
     transform_index_to_disease = {row['index']: row['disease_name'] for _, row in data.iterrows()}
     ```

---

## **Deployment Instructions**

1. **Prepare for Deployment**:
   - Update `production_settings.py` for production configurations.
   - Set `DEBUG = False` and configure `ALLOWED_HOSTS`.

2. **Deploy to Heroku**:
   - Install Heroku CLI: [heroku.com/cli](https://devcenter.heroku.com/articles/heroku-cli).
   - Log in to Heroku:
     ```bash
     heroku login
     ```
   - Create a new app:
     ```bash
     heroku create your-app-name
     ```
   - Push code to Heroku:
     ```bash
     git push heroku main
     ```
   - Run migrations on Heroku:
     ```bash
     heroku run python manage.py migrate
     ```
   - Collect static files:
     ```bash
     heroku run python manage.py collectstatic
     ```

3. **Set Config Vars**:
   Set sensitive variables as Heroku config vars:
   ```bash
   heroku config:set DJANGO_SECRET_KEY=your_secret_key
   heroku config:set DJANGO_ALLOWED_HOSTS=your-app-name.herokuapp.com
   heroku config:set DJANGO_DATABASE_URL=postgres://username:password@host:port/dbname
   heroku config:set AWS_ACCESS_KEY_ID=your_aws_access_key_id
   heroku config:set AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   heroku config:set AWS_STORAGE_BUCKET_NAME=your_s3_bucket_name
   heroku config:set DJANGO_EMAIL_USER=your_email@gmail.com
   heroku config:set DJANGO_EMAIL_PASSWORD=your_email_password
   ```

4. **Enable HTTPS**:
   Heroku automatically enables HTTPS with its free SSL certificate.

5. **Monitor Logs**:
   Check logs for debugging:
   ```bash
   heroku logs --tail
   ```

---

## **Contributing**

To contribute to TogetherSO:
1. Fork the repository.
2. Clone your forked repository:
   ```bash
   git clone https://github.com/your-fork-url/togetherso.git
   ```
3. Create a new branch:
   ```bash
   git checkout -b feature/new-feature
   ```
4. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Add new feature"
   ```
5. Push your changes:
   ```bash
   git push origin feature/new-feature
   ```
6. Submit a pull request.

---

## **License**

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## **Additional Notes**

- **Email Gateway**:
  - Configure the email backend in `production_settings.py` for sending verification emails.
  - Example Gmail configuration:
    ```python
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('DJANGO_EMAIL_USER')
    EMAIL_HOST_PASSWORD = os.getenv('DJANGO_EMAIL_PASSWORD')
    ```

- **Media Storage**:
  - Use Amazon S3 or Google Cloud Storage for media uploads.
  - Update `production_settings.py` with your AWS credentials:
    ```python
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = 'your-s3-bucket-name'
    MEDIA_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    ```

- **Improving Accuracy**:
  - Fine-tune the AI model using additional datasets.
  - Update the `CNN.py` file with improvements.

---

This `README.md` provides a comprehensive guide for setting up, running, and deploying the TogetherSO application. Let me know if you'd like further refinements!