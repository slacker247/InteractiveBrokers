import os
import sys
import mysql.connector
import traceback

class InteractiveBrokersDB:
    def __init__(self):
        self.UserName = ""
        self.Password = ""
        self.DBHost = ""
        self.DBPort = 0
        self.DBName = ""
        pass

    def loadSettings(self, filename:str):
        with open(filename, 'r') as f:
            for line in f:
                parts = line.split('=')
                if parts[0] == "user_name":
                    self.UserName = str(parts[1]).strip()
                if parts[0] == "password":
                    self.Password = str(parts[1]).strip()
                if parts[0] == "db_host":
                    self.DBHost = str(parts[1]).strip()
                if parts[0] == "db_port":
                    self.DBPort = int(parts[1])
                if parts[0] == "db_name":
                    self.DBName = str(parts[1]).strip()
                pass
        pass

    def getDB(self):
        db_conn = None
        db_conn = mysql.connector.connect(
            host=self.DBHost,
            port=self.DBPort,
            user=self.UserName,
            passwd=self.Password,
            pool_name="db_conns",
            pool_size=32,
            db=self.DBName)
        db_conn.autocommit = True
        return db_conn

    # Specify variables using %s or %(name)s parameter style.
    def executeSql(self, sql, parms=None):
        tries = 0
        id = -1
        cursor = None
        error_msg = ""
        while tries < 5:
            try:
                mydb = self.getDB()
                cursor = mydb.cursor(buffered=True)
                tries += 1
                if not parms == None:
                    cursor.execute(sql, parms)
                else:
                    cursor.execute(sql)
                id = cursor.rowcount
                mydb.commit()
                break
            except Exception as ex:
                error_msg = str(ex)
                if "not available" in str(ex) or "bytearray index" in str(ex):
                    time.sleep(0.120)
                else:
                    print("executeSql - {}".format(ex))
                    for strTrace in traceback.format_stack():
                        print(strTrace)
                    print("Parms: {}".format(parms))
                    print("SQL: {}".format(sql))
                print("MySQL Tries: {}".format(tries))
            if cursor != None:
                cursor.close()
        mydb.close()
            
        if tries > 4:
            for strTrace in traceback.format_stack():
                print(strTrace)
            print("mysql failed to execute - {}".format(error_msg))
            print(sql)
            print()
        return id

    def executeQuery(self, sql, parms=None):
        results = None
        mydb = self.getDB()
        #mydb.reset_session()
        cursor = mydb.cursor(buffered=True, dictionary=True)
        if not parms == None:
            cursor.execute(sql, parms)
        else:
            cursor.execute(sql)

        results = cursor.fetchall()
        mydb.commit()

        cursor.close()
        mydb.close()
        return results

if __name__ == "__main__":
    settingsFile = "Settings.ini"
    db = InteractiveBrokersDB()
    db.loadSettings(settingsFile)
    testCase = 1
    if testCase == 0:
        sql = "INSERT INTO `interactive_brokers`.`symbols` "
        sql += "( "
        sql += "`name`, "
        sql += "`symbol`, "
        sql += "`active`) "
        sql += "VALUES "
        sql += "( "
        sql += "'Microsoft', "
        sql += "'MSFT', "
        sql += "true); "

        results = db.executeSql(sql)
    if testCase == 1:
        sql = "Select * from `interactive_brokers`.`symbols`;"
        results = db.executeQuery(sql)
        for row in results:
            print("row: {}".format(row))
    print("\n\nFinished.")
    pass




