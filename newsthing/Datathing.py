import logging
import sqlite3
from abc import ABCMeta, abstractmethod


class Datathing(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def create(cls): pass

    @abstractmethod
    def close(self): pass

    @abstractmethod
    def upsert_newsgroups(self, newsgroups): pass

    @abstractmethod
    def get_newsgroups(self): pass

    @abstractmethod
    def get_messages(self, group): pass

    @abstractmethod
    def update_messages(self, group, batch): pass

    @abstractmethod
    def stat_group(self, group): pass


# noinspection SqlResolve
class SQLite(Datathing):
    _db: sqlite3.Connection = None
    _server: str = None
    
    @classmethod
    def create(cls, *args, **kwargs):
        return cls(
            database=kwargs["database"],
            server=kwargs["server"]
        )

    def __init__(
            self,
            database,
            server
            ):
        self._db = sqlite3.connect(database)
        self._db.execute("pragma journal_mode=wal")
        self._server = server
        self._db.execute(
            f"""
            create table if not exists main.newsgroups (
                server text,
                newsgroup text,
                
                primary key (server, newsgroup)
            )
            """
        )
    
    def _group_table_name(self, group):
        return f"{self._server}.{group}".replace(".", "_")

    def close(self):
        self._db.close()

    def upsert_newsgroups(self, newsgroups):
        self._db.executemany(
            """
            insert into main.newsgroups (server, newsgroup)
            values (?, ?)
            on conflict do nothing
            """,
            map(lambda g: (self._server, g.group,), newsgroups)
        )
        self._db.commit()
    
    def get_newsgroups(self):
        records = self._db.execute(
            """
            select newsgroup from main.newsgroups where server = ?
            """,
            (self._server,)
        )
        newsgroups = [*map(lambda row: row[0], records)]
        return newsgroups

    def get_messages(self, group, **kwargs):
        group_table = self._group_table_name(group)
        wheres, whargs = [], []
        if kwargs:
            for col_name in [
                "article",
                "message_id",
                "date",
                "subject",
                "from",
            ]:
                if wharg := kwargs.get(col_name):
                    applied = False
                    for op in ["> ", "< ", ">= ", "<= ", '= ', '!= ', '<> ',
                               "is not ", "is ", "like ", "glob "]:
                        if wharg.startswith(op):
                            wheres.append(f" [{col_name}] {op} ? ")
                            whargs.append(wharg[len(op):])
                            applied = True
                            break
                    if type(wharg) is tuple:
                        wheres.append(f" [{col_name}] between ? and ? ")
                        wh_min, wh_max = wharg
                        whargs.append(wh_min)
                        whargs.append(wh_max)
                        applied = True
                    if type(wharg) is list:
                        wheres.append(f" [{col_name}] in "
                                      f"({','.join(len(wharg) * '?')}) ")
                        for whitem in wharg:
                            whargs.append(whitem)
                        applied = True
                    if not applied:
                        wheres.append(f" [{col_name}] glob '*' || ? ")
                        whargs.append(wharg)

        messages = self._db.execute(f"""
            select article, --integer
                message_id, --text
                [date], --text
                subject, --text
                [from], --text
                organization, --text
                path, --text
                newsgroups, --text
                [references], --text
                expires, --text
                distribution --text
            from {group_table}
            {'where' if wheres else ''}
                {' and '.join(wheres)}
            order by article asc
        """, (*whargs,)).fetchall()
        return messages

    def update_messages(self, group, batch):
        group_table = self._group_table_name(group)
        number_updated = 0
        logging.debug(f"Updating messages in table '{group_table}'.")
        for hdr, vals in batch.items():
            if vals:
                rows = self._db.total_changes
                column = hdr.lower().replace("-", "_")
                self._db.executemany(
                    f"""
                        insert into {group_table}
                            (article, [{column}])
                        values (?, ?)
                        on conflict(article) do update
                            set [{column}]=excluded.[{column}]
                    """,
                    vals
                )
                rows = self._db.total_changes - rows
                logging.debug(f"Inserted or updated {rows} rows "
                              f"for header '{hdr}'.")
                number_updated += len(vals)
        self._db.commit()
        return number_updated

    def stat_group(self, group):
        group_table = self._group_table_name(group)
        self._db.execute(
            f"""
            create table if not exists {group_table} (
                article integer not null,
                message_id text,
                [date] text,
                subject text,
                [from] text,
                organization text,
                path text,
                newsgroups text,
                [references] text,
                expires text,
                distribution text,
                
                primary key (article desc)
            )
            """
        )
        self._db.execute(
            f"""
            create index if not exists {group_table}_idx_subject
            on {group_table} (
                subject collate nocase
            )
            """
        )
        self._db.execute(
            f"""
            create index if not exists {group_table}_idx_article
            on {group_table} (
                article
            )
            """
        )
        self._db.execute(
            f"""
            create index if not exists {group_table}_idx_message_id
            on {group_table} (
                message_id
            )
            """
        )
        self._db.execute(
            f"""
            create index if not exists {group_table}_idx_from
            on {group_table} (
                [from] collate nocase
            )
            """
        )
        self._db.execute(
            f"""
            create index if not exists {group_table}_idx_date
            on {group_table} (
                [date]
            )
            """
        )
        self._db.commit()
        article_min, article_max = self._db.execute(f"""
            select coalesce(min(article), 0), coalesce(max(article), 0)
            from {group_table}
        """).fetchone()
        return article_min, article_max