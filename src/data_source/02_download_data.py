import os
import shutil

# 1. Define your secret scope name
SECRET_SCOPE = "portfolio_secret"

# 2. Retrieve credentials securely from Databricks Secrets
os.environ['KAGGLE_USERNAME'] = dbutils.secrets.get(scope=SECRET_SCOPE, key="KAGGLE_USERNAME")
os.environ['KAGGLE_KEY'] = dbutils.secrets.get(scope=SECRET_SCOPE, key="KAGGLE_API_TOKEN")

# 2. Create a temporary folder inside your permitted /Workspace directory
# os.getcwd() gets your current notebook's location, which is allowed.
workspace_tmp = os.path.join(os.getcwd(), "paysim_temp")
os.makedirs(workspace_tmp, exist_ok=True)

# 3. Download and unzip to the Workspace directory
print("Downloading and unzipping dataset...")
os.system(f"kaggle datasets download -d ealaxi/paysim1 -p {workspace_tmp} --unzip")

# 4. Define your Unity Catalog Volume path
uc_volume_path = "/Volumes/portfolio_catalog/compliance_project/raw_data"

# 5. Move the unzipped CSV to the Unity Catalog Volume
# Note: The 'file:' prefix tells Databricks it's coming from the local Workspace
local_csv_path = os.path.join(workspace_tmp, "PS_20174392719_1491204439457_log.csv")
volume_csv_path = f"{uc_volume_path}/paysim_raw.csv"

print("Moving file to Unity Catalog Volume...")
dbutils.fs.cp(f"file:{local_csv_path}", volume_csv_path)

# 6. Clean up the temporary workspace folder to free up space
shutil.rmtree(workspace_tmp)

print(f"Success! Dataset moved to Unity Catalog Volume at: {volume_csv_path}")