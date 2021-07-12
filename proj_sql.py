import mysql.connector
import csv
import re
import web_scraping as ws


def connect_mysql():
    # establish connection to the local db
    # the user has root privilages
    my_db = mysql.connector.connect(
      host="localhost",
      user="ceid",
      passwd="1SafePass"
    )
    mycursor = my_db.cursor()
    # drop the old database
    mycursor.execute("DROP DATABASE IF EXISTS pythonDB;")
    # create a db to connect to
    mycursor.execute("CREATE DATABASE IF NOT EXISTS pythonDB;")
    # use the db
    mycursor.execute("USE pythonDB")
    return my_db


# create all those tables that are constant, no matter which file you load
# the drops are not required, since I drop the whole base on connection
def create_default_tables(connection):
    mycursor = connection.cursor()
    mycursor.execute("DROP TRIGGER IF EXISTS country_year_after_country")
    mycursor.execute("DROP TABLE IF EXISTS country_year;")
    mycursor.execute("DROP TABLE IF EXISTS year;")
    mycursor.execute("DROP TABLE IF EXISTS country;")

    mycursor.execute("CREATE TABLE country ("
                     "cname VARCHAR(15) NOT NULL,"
                     "PRIMARY KEY (cname)"
                     ");")
    mycursor.execute("CREATE TABLE year ("
                     "year_val INT NOT NULL,"
                     "PRIMARY KEY (year_val)"
                     ");")
    mycursor.execute("CREATE TABLE country_year ("
                     "id INT AUTO_INCREMENT PRIMARY KEY,"
                     "country VARCHAR(15),"
                     "FOREIGN KEY (country) REFERENCES country(cname)"
                     "ON UPDATE CASCADE,"
                     "year INT,"
                     "FOREIGN KEY (year) REFERENCES year(year_val)"
                     "ON UPDATE CASCADE"
                     ");")
    # trigger that will insert all records into the country_year table
    mycursor.execute("CREATE TRIGGER country_year_after_country "
                     "AFTER INSERT ON country "
                     "FOR EACH ROW "
                     "  BEGIN "
                     "  DECLARE done INT DEFAULT FALSE;"
                     "  DECLARE y INT;"
                     "  DECLARE cur CURSOR FOR SELECT * FROM year ;"
                     "  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;"
                     "  OPEN cur;"
                     "  year_loop: LOOP "
                     "      FETCH cur INTO y;"
                     "      IF done THEN "
                     "          LEAVE year_loop;"
                     "      END IF;"
                     "  INSERT INTO country_year (country, year) VALUES (NEW.cname, y);"
                     "  END LOOP;"
                     "  CLOSE cur;"
                     "END")


# the only dynamic thing about them is the name
# I chose varchar(100) to save the data so I don't have to remove ":"
def create_dynamic_table(connection, table_name):
    mycursor = connection.cursor()
    mycursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    mycursor.execute(f"CREATE TABLE {table_name} ("
                     f"id INT AUTO_INCREMENT PRIMARY KEY,"
                     f"cy_id INT NOT NULL,"
                     f"value VARCHAR(100),"
                     f"c_resid ENUM('FOR', 'NAT', 'TOTAL'),"
                     f"FOREIGN KEY (cy_id) REFERENCES country_year(id)"
                     f"ON UPDATE CASCADE"
                     f");")


# given a connection, a table and the record I want to insert returns
# true is record not in the table and false if record already exists in the table
# TODO: FIX: new_record must be a string, fix it so it may be a list (not important)
def can_insert(connection, table_name, new_record):
    mycursor = connection.cursor()
    mycursor.execute(f"SELECT * FROM {table_name}")
    records = mycursor.fetchall()
    for record in records:
        for value in record:
            if str(value) == str(new_record):
                return 0
    return 1


# returns the id which corresponds to country, year record in coutry_year table
# could be avoided if I only inserted on the dynamic tables (tin00174, tin00175)
# with a JOIN
def get_country_year_id(connection, country, year):
    mycursor = connection.cursor()
    mycursor.execute("SELECT id FROM country_year WHERE country = %s AND year = %s", (country, year))
    return mycursor.fetchone()[0]


# remember that the values need to be in a tuple form
# the function below loads all tables using the data in filename(csv format)
def load_tables(connection, filename):
    # use the filename (ex. tin00174) in order to name the table you are creating
    fname = ws.spilt_filename(filename)[1]
    create_dynamic_table(connection, fname)
    # get the cursor that you will execute sql commands with
    mycursor = connection.cursor()
    inp = open(filename, 'r')
    csv_inp = csv.DictReader(inp)
    # insert years into sql table year
    # clean the first line (remove the 2 leftmost strings "c_resid", "geo" and the '\n' at the end of the line)
    years = inp.readline().split(',')[2:]
    years = [re.sub(r"\n", "", year) for year in years]
    # insert the years into the correct table (if not already inserted)
    for year in years:
        if can_insert(connection, "year", year):
            mycursor.execute("INSERT INTO year (year_val) VALUES (%s)", (year,))
    # get back to the beggining of the file
    inp.seek(0)
    # for each line (except the first one, csv library)
    for row in csv_inp:
        cname = row["geo"]
        # insert the country names into the correct table (if not already inserted)
        if can_insert(connection, "country", cname):
            mycursor.execute("INSERT INTO country (cname) VALUES (%s)", (cname,))
        # insert the data into the dynamic table I created earlier in this function
        for year in years:
            cy_id = get_country_year_id(connection, cname, year)
            mycursor.execute(f"INSERT INTO {fname} (cy_id, value, c_resid) VALUES (%s, %s, %s)", (int(cy_id), str(row[str(year)]), str(row["c_resid"])))
    # save any changes I made (only need to commit once on each session)
    connection.commit()
    # close your files!
    inp.close()
