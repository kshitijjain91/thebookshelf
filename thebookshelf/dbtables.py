import pymysql
import dbconfig

# create users table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists users
                        (user_id int not null auto_increment primary key,
                        email varchar(200), username varchar(200),
                        password varchar(300));''')

        conn.commit()

except Exception as e:
    print ("Exception in creating table:{0}".format(e))
finally:
    conn.close()

# create books table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists books
            (book_id int not null auto_increment primary key,
            name varchar(100) not null,
            author varchar(200),
            description varchar(3000),
            type varchar(20),
            size int,
            file mediumblob not null);''')
        conn.commit()
except Exception as e:
    print("Exeption in creating table: {0}".format(e))
finally:
    conn.close()

# create user_books table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists user_books
            (upload_id int not null auto_increment primary key,
            user_id int,
            book_id int,
            foreign key (user_id) references users(user_id),
            foreign key (book_id) references books(book_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()


# create reading list table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists reading_list
            (user_id int,
            book_id int,
            foreign key (user_id) references users(user_id),
            foreign key (book_id) references books(book_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()


# create likes table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists likes
            (user_id int,
            book_id int,
            foreign key (user_id) references users(user_id),
            foreign key (book_id) references books(book_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()

# create requests table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists requests
            (user_id int,
            book_name varchar(100),
            author_name varchar(100),
            description varchar(500),
            foreign key (user_id) references users(user_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()