// init-mongo.js

// Classes are not recommended in docker init scripts
// due to async problems from constructor/method.

// --- Configuration ---
// These variables are loaded from the environment.

// NOT required. This is the root user for MongoDB that is
// created by the official MongoDB Docker image.
// const user_root = process.env.MONGODB_INITDB_ROOT_USERNAME;
// const user_root_pwd = process.env.MONGODB_INITDB_ROOT_PASSWORD;

const user_dbadmin = process.env.MONGODB_ADMIN_DBADMIN;
const user_dbadmin_pwd = process.env.MONGODB_ADMIN_DBADMIN_PASSWORD;

const db_name1 = process.env.MONGODB_DB_NAME1;
const user_app1 = process.env.MONGODB_USER_APP1;
const user_app1_pwd = process.env.MONGODB_USER_APP1_PASSWORD;
const user_reader1 = process.env.MONGODB_USER_READER1;
const user_reader1_pwd = process.env.MONGODB_USER_READER1_PASSWORD;

const db_name2 = process.env.MONGODB_DB_NAME2;
const user_app2 = process.env.MONGODB_USER_APP2;
const user_app2_pwd = process.env.MONGODB_USER_APP2_PASSWORD;
const user_reader2 = process.env.MONGODB_USER_READER2;
const user_reader2_pwd = process.env.MONGODB_USER_READER2_PASSWORD;

const default_collection =
  process.env.DEFAULT_COLLECTION || "default_collection";

function envChecker() {
  // 1. Input Validation: Fail fast if critical secrets are missing.
  if (
    !user_dbadmin ||
    !user_dbadmin_pwd ||
    !db_name1 ||
    !user_app1 ||
    !user_app1_pwd ||
    !user_reader1 ||
    !user_reader1_pwd ||
    !db_name2 ||
    !user_app2 ||
    !user_app2_pwd ||
    !user_reader2 ||
    !user_reader2_pwd
  ) {
    throw new Error(
      "Missing critical environment variables for database initialization."
    );
  }
}

function helperCreateUser(targetDB, username, password, roles) {
  targetDB.createUser({
    user: username,
    pwd: password,
    roles: roles,
  });
}

function helperCreateAdminUser(adminDB, username, password) {
  try {
    helperCreateUser(adminDB, username, password, [
      { role: "readWriteAnyDatabase", db: "admin" },
      { role: "userAdminAnyDatabase", db: "admin" },
    ]);
    print(`Successfully created dbadmin user '${username}'.`);
  } catch (e) {
    print(`ERROR creating user ${username}: ${e.message}`);
  }
}

function helperCreateAppUser(targetDB, role_targetDbName, username, password) {
  try {
    helperCreateUser(targetDB, username, password, [
      { role: "dbAdmin", db: role_targetDbName },
      { role: "readWrite", db: role_targetDbName },
    ]);
    print(`Successfully created app user '${username}'.`);
  } catch (e) {
    print(`ERROR creating user ${username}: ${e.message}`);
  }
}

function helperCreateReaderUser(
  targetDB,
  role_targetDbName,
  username,
  password
) {
  try {
    helperCreateUser(targetDB, username, password, [
      { role: "read", db: role_targetDbName },
    ]);
    print(`Successfully created app user '${username}'.`);
  } catch (e) {
    print(`ERROR creating user ${username}: ${e.message}`);
  }
}
// --- Main Execution ---
function main() {
  print("--- Starting MongoDB Initialization ---");
  envChecker();

  print(` >> initializing db(${db_name1})`);
  const targetDb = db.getSiblingDB(db_name1);
  targetDb.createCollection(default_collection);
  helperCreateAppUser(targetDb, db_name1, user_app1, user_app1_pwd);
  helperCreateReaderUser(targetDb, db_name1, user_reader1, user_reader1_pwd);

  print(` >> initializing db(${db_name2})`);
  const targetDb2 = db.getSiblingDB(db_name2);
  targetDb2.createCollection(default_collection);
  helperCreateAppUser(targetDb2, db_name2, user_app2, user_app2_pwd);
  helperCreateReaderUser(targetDb2, db_name2, user_reader2, user_reader2_pwd);

  print(" >> initializing db(admin)");
  const adminDb = db.getSiblingDB("admin");
  helperCreateAdminUser(adminDb, user_dbadmin, user_dbadmin_pwd);

  print("--- MongoDB Initialization Complete ---");
}
// Run the main function
main();
