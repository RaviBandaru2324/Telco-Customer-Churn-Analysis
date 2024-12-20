# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from imblearn.over_sampling import SMOTE
from ydata_profiling import ProfileReport
import sweetviz as sv
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve, roc_auc_score

# Load the dataset
data = pd.read_csv('/content/telco-customer-churn.csv')

data.head()

data.columns

data.isnull().sum()

#Display categorical columns
categorical_columns = data.select_dtypes(exclude=[np.number]).columns.tolist()
print("Categorical Coulumns:", categorical_columns)

#Display Numeric Columns
numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
print("Numeric Columns:", numeric_columns)

# Data Preprocessing
# Impute Missing Values
data.ffill(inplace=True)
data.isnull().sum()

# Encode Categorical Variables
categorical_cols = data.select_dtypes(include=['object']).columns
for col in categorical_cols:
    data[col] = LabelEncoder().fit_transform(data[col])

# Convert MonthlyCharges from float64 to int64
data['MonthlyCharges'] = data['MonthlyCharges'].astype('int64')
data.dtypes

#Finding Outliers
from scipy.stats import zscore
numeric_columns = ['tenure', 'MonthlyCharges', 'TotalCharges']

def outliers_zscore(data, threshold=3):
  z_score = np.abs(zscore(data))
  outliers = np.where(z_score > threshold)
  return outliers

outliers_tenure = outliers_zscore(data['tenure'])
outliers_monthlycharges = outliers_zscore(data['MonthlyCharges'])
outliers_totalcharges = outliers_zscore(data['TotalCharges'])

print(f'Outliers in Tenure: {len(outliers_tenure)}')
print(f'Outliers in Monthly Charges: {len(outliers_monthlycharges)}')
print(f'Outliers in Total Charges: {len(outliers_totalcharges)}')

#Performing EDA Visualizations
for col in numeric_columns:
    plt.figure(figsize=(8,6))
    sns.boxplot(x=data[col])
    plt.title(f'Boxplot of {col}')
    plt.show()

#Countplot of Churn
sns.countplot(x='Churn', data=data)
plt.title('Churn Distribution')
plt.show()

# Dependency Plots for variables vs target
#Barplot of Tenure vs Churn plot
plt.figure(figsize=(8,6))
sns.barplot(x='Churn', y='tenure', data=data)
plt.title("Tenure vs Churn")
plt.show()

#Histogram of MonthlyCharges vs Churn
r=sns.FacetGrid(data, hue="Churn", height=6, aspect=2)
r.map(sns.histplot, 'MonthlyCharges', bins=30, kde=False)
r.add_legend()
plt.title('Histogram of MonthlyCharges vs Churn')
plt.show()

#Countplot of Contract type on Churn
sns.countplot(x='Contract', hue='Churn', data=data)
plt.title('Contract Type vs Churn')
plt.show()

# Correlation Heat Map for numeric columns
correlation_matrix = data.corr()
plt.figure(figsize=(12,8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Matrix')
plt.show()

# Feature Importance
correlation_with_churn = data.corr()['Churn'].sort_values(ascending=False)
print(correlation_with_churn)

#Split data into training and testing sets
X= data.drop(columns=['Churn', 'customerID'])
y=data['Churn']
X_train, X_test, y_train, y_test=train_test_split(X,y,test_size=0.2, random_state=42)
#Combining training data and test data
train_data = pd.concat([X_train, y_train], axis=1)
test_data = pd.concat([X_test, y_test], axis=1)
#Generating html report of train and test data using sweetviz compare
report = sv.compare([train_data, "Training Data"], [test_data, "Testing Data"])
report.show_html('sweetviz_analysis.html')

# Generate the Pandas Profiling report
profile = ProfileReport(data, title="Telco Customer Churn - Pandas Profiling Report", explorative=True)

# Save the report to an HTML file
profile.to_file("pandas_profiling_report.html")

print("Pandas Profiling report generated: 'pandas_profiling_report.html'")

# Generate the SweetViz report
sweetviz_report = sv.analyze(data)

# Save the report to an HTML file
sweetviz_report.show_html("sweetviz_report.html")
print("SweetViz report generated: 'sweetviz_report.html'")

# Add a constant to the model (intercept)
X1 = sm.add_constant(X)

# Fit the logistic regression model
model = sm.Logit(y, X1)
result = model.fit()

# Print the summary of the regression
print(result.summary())

# Feature Scaling
scaler = StandardScaler()
X = scaler.fit_transform(data.drop(columns='Churn'))
y = data['Churn']

# Address Imbalance with SMOTE
smote = SMOTE(random_state=42)
X_smote, y_smote=smote.fit_resample(X,y)

# SPlitting Training and Testing data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train_smote, X_test_smote, y_train_smote, y_test_smote = train_test_split(X_smote, y_smote, test_size=0.2, random_state=42)
# Model Training and Evaluation Function
def evaluate_model(model, X_train, y_train, X_test, y_test, model_name="Model"):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"--- {model_name} Performance ---")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Precision:", precision_score(y_test, y_pred))
    print("Recall:", recall_score(y_test, y_pred))
    print("F1-Score:", f1_score(y_test, y_pred))
    print()

# Models to Train
models = {
    "Naive Bayes": GaussianNB(),
    "Logistic Regression": LogisticRegression(max_iter=200),
    "Random Forest": RandomForestClassifier(random_state=42),
    "XGBoost": XGBClassifier( eval_metric='logloss')
}

# Initialize an empty list to store results
results = []

# Model training and evaluation without visualizations
for model_name, model in models.items():
    # Fit and predict on original data
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Calculate metrics for original data
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # Store the results for original data
    results.append({
        'Model': model_name,
        'Data Type': 'Original',
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1
    })

    # Fit and predict on SMOTE data
    model.fit(X_train_smote, y_train_smote)
    y_pred_smote = model.predict(X_test_smote)

    # Calculate metrics for SMOTE data
    accuracy_smote = accuracy_score(y_test_smote, y_pred_smote)
    precision_smote = precision_score(y_test_smote, y_pred_smote)
    recall_smote = recall_score(y_test_smote, y_pred_smote)
    f1_smote = f1_score(y_test_smote, y_pred_smote)

    # Store the results for SMOTE data
    results.append({
        'Model': model_name,
        'Data Type': 'SMOTE',
        'Accuracy': accuracy_smote,
        'Precision': precision_smote,
        'Recall': recall_smote,
        'F1-Score': f1_smote
    })

# Create a DataFrame from the results list
results_df = pd.DataFrame(results)

# Display the results DataFrame
print("\nModel Evaluation Results:")
print(results_df)

# Define the parameter grids for each model
rf_param_grid = {
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'bootstrap': [True, False]
}

xgb_param_grid = {
    'learning_rate': [0.01, 0.1, 0.2, 0.3],
    'max_depth': [3, 5, 7, 10],
    'n_estimators': [50, 100, 200, 300],
    'subsample': [0.5, 0.7, 1.0],
    'colsample_bytree': [0.5, 0.7, 1.0]
}

# Initialize the models
rf_model = RandomForestClassifier(random_state=42)
xgb_model = XGBClassifier(eval_metric='logloss', random_state=42)

# Initialize RandomizedSearchCV for each model
rf_random_search = RandomizedSearchCV(estimator=rf_model, param_distributions=rf_param_grid,
                                      n_iter=20, cv=5, scoring='recall', random_state=42, n_jobs=-1)

xgb_random_search = RandomizedSearchCV(estimator=xgb_model, param_distributions=xgb_param_grid,
                                       n_iter=20, cv=5, scoring='recall', random_state=42, n_jobs=-1)

# Perform RandomizedSearchCV for Random Forest
rf_random_search.fit(X_train_smote, y_train_smote)
print("Best Parameters for Random Forest:", rf_random_search.best_params_)
best_rf_model = rf_random_search.best_estimator_

# Perform RandomizedSearchCV for XGBoost
xgb_random_search.fit(X_train_smote, y_train_smote)
print("Best Parameters for XGBoost:", xgb_random_search.best_params_)
best_xgb_model = xgb_random_search.best_estimator_

# Evaluate tuned models
print("\n--- Evaluation of Tuned Random Forest Model ---")
evaluate_model(best_rf_model, X_train_smote, y_train_smote, X_test_smote, y_test_smote, model_name="Tuned Random Forest")

print("\n--- Evaluation of Tuned XGBoost Model ---")
evaluate_model(best_xgb_model, X_train_smote, y_train_smote, X_test_smote, y_test_smote, model_name="Tuned XGBoost")

# Function to plot Confusion Matrix
def plot_confusion_matrix(y_true, y_pred, model_name):
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Spectral", cbar=False)
    plt.title(f"{model_name} Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.show()

# Function to plot Precision-Recall Curve
def plot_precision_recall_curve(model, X_test, y_test, model_name):
    y_probs = model.predict_proba(X_test)[:, 1]  # Probabilities for the positive class
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    plt.plot(recall, precision, label=f'{model_name}')
    plt.title(f'{model_name} Precision-Recall Curve')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.legend(loc="lower left")
    plt.show()

# Plotting all visualizations for each model
for model_name, model in models.items():
    # Fit and predict on original data
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"Visualizations for {model_name}")
    plot_confusion_matrix(y_test, y_pred, model_name=model_name)
    plot_precision_recall_curve(model, X_test, y_test, model_name=model_name)

    # Fit and predict on SMOTE data
    model.fit(X_train_smote, y_train_smote)
    y_pred_smote = model.predict(X_test_smote)

    print(f"Visualizations for {model_name} (SMOTE)")
    plot_confusion_matrix(y_test_smote, y_pred_smote, model_name=model_name + " (SMOTE)")
    plot_precision_recall_curve(model, X_test_smote, y_test_smote, model_name=model_name + " (SMOTE)")

# AUC for Original Data

plt.figure(figsize=(12, 8))
for model_name, model in models.items():
    model.fit(X_train, y_train)

    # Predict probabilities for the positive class
    y_proba = model.predict_proba(X_test)[:, 1]

    # Calculate ROC curve
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)

    # Calculate AUC score
    auc_score = roc_auc_score(y_test, y_proba)

    # Plot ROC curve
    plt.plot(fpr, tpr, label=f'{model_name} (Original AUC = {auc_score:.2f})')

# Plotting the diagonal line (chance)
plt.plot([0, 1], [0, 1], 'k--', label='Random Chance')

# Show the curve
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for Original Data')
plt.legend(loc='lower right')
plt.grid()
plt.show()

# AUC for SMOTE Data

plt.figure(figsize=(12, 8))
for model_name, model in models.items():
    model.fit(X_train_smote, y_train_smote)

    # Predict probabilities for the positive class
    y_proba = model.predict_proba(X_test_smote)[:, 1]

    # Calculate ROC curve
    fpr, tpr, thresholds = roc_curve(y_test_smote, y_proba)

    # Calculate AUC score
    auc_score = roc_auc_score(y_test_smote, y_proba)

    # Plot ROC curve
    plt.plot(fpr, tpr, label=f'{model_name} (SMOTE AUC = {auc_score:.2f})')

# Plotting the diagonal line (chance)
plt.plot([0, 1], [0, 1], 'k--', label='Random Chance')

# Show the curve
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for SMOTE Data')
plt.legend(loc='lower right')
plt.grid()
plt.show()
