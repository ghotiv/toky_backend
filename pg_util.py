import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
# from loguru import logger

@contextmanager
def get_conn(self):
    try:
        conn = self.getconn()
        with conn as real_conn:
            yield real_conn
    except:
        raise
    finally:
        self.putconn(conn)

class Postgresql(object):
    """docstring for postgresql"""
    def __init__(self,host,db,user,pwd,port=5432):
        self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=100,
                host=host,
                database=db,
                user=user,
                password=pwd,
                port=port
            )

    def query(self, sql):
        with get_conn(self._pool) as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql)
            conn.commit()
            return cur.fetchall()

    def execute(self, sql, return_id=False):
        with get_conn(self._pool) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            if return_id:
                res = cur.fetchone()[0]
                
            else:
                res = cur.rowcount
            return res

    def insert(self, table, tdict, return_id=False):
        column = ''
        value = ''
        for key in tdict:
            # print(key,tdict[key])
            column += ',' + key
            value += "','" + str(tdict[key])
        column = column[1:]
        value = value[2:] + "'"
        sql = "insert into %s(%s) values(%s)" % (table, column, value)
        print(sql)
        if return_id:
            sql = sql + ' RETURNING id;'
        # print(sql)
        # logging.info('insert sql: %s' % sql)
        return self.execute(sql,return_id=return_id)

    def update(self, table, tdict, condition=''):
        if not condition:
            # logging.info("must have update condition")
            return
        else:
            condition = 'where ' + condition
        value = ''
        for key in tdict:
            value += ",%s='%s'" % (key, tdict[key])
        value = value[1:]
        sql = "update %s set %s %s" % (table, value, condition)
        print(condition,sql)
        # logging.info('update sql: %s'%sql)
        # logging.info('success update sql: %s' % sql)
        return self.execute(sql)


