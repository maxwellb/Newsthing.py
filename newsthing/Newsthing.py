import datetime
from nntplib import NNTP_SSL as NNTP
from .Datathing import Datathing, SQLite as DatathingImpl
import dateutil.parser
import logging
import ssl


# noinspection SqlResolve
class Newsthing:
    _dt: Datathing = None
    _news: NNTP = None
    _newsgroup: str = None
    _server: str = None
    
    def __init__(
            self,
            database,
            /,
            server,
            *,
            port=443,
            connect=True):
        self._dt = DatathingImpl.create(
            database=database,
            server=server
        )
        self._server = server
        if connect:
            self.connect(port=port)
    
    def connect(self, port=443) -> NNTP:
        reconnect, response, date = False, None, None
        if self._news:
            # noinspection PyBroadException
            try:
                response, date = self._news.date()
            except Exception:
                reconnect = True
            if not date:
                reconnect = True
        else:
            reconnect = True
        if reconnect:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.set_ciphers("HIGH:!DH")
            self._news = NNTP(host=self._server,
                              port=port,
                              ssl_context=ssl_ctx,
                              usenetrc=True)
        return self._news
    
    def close(self) -> str:
        self._dt.close()
        try:
            return self._news.quit()
        except EOFError:
            return ""
        except AttributeError:
            return ""
    
    def groups(self, /, refresh=False):
        if refresh:
            response, resp_list = self._news.list()
            self._dt.upsert_newsgroups(resp_list)
        groups = self._dt.get_newsgroups()
        return groups
    
    def retrieve(self, group, min_article, max_article):
        header_names = [
            "Message-Id",
            "Date",
            "Subject",
            "From",
            "Organization",
            "Path",
            "Newsgroups",
            "References",
            "Expires",
            "Distribution",
            # "X-Ufhash",
            # "X-Received-Bytes",
        ]
        logging.info(
            "Retrieving messages #%d - #%d for group '%s'.",
            min_article,
            max_article,
            group
        )
        news = self.connect()
        news.group(group)
        time_begin = datetime.datetime.now()
        batch = {}
        for hdr in header_names:
            resp, values = news.xhdr(hdr, f"{min_article}-{max_article}")
            if hdr == "Date":
                values = map(
                    lambda x: (x[0], dateutil.parser.parse(x[1]).isoformat(),),
                    values)
            batch[hdr] = [*values]
        elapsed = datetime.datetime.now() - time_begin
        logging.info(
            "Downloaded %d article headers took [%s].",
            len(range(min_article, max_article+1)),
            elapsed
        )
        return batch

    def messages(self, group, /, older=0, newer=1000, *, refresh=False,
                 **kwargs):
        current_max_article: int
        current_min_article: int
        live_max_article: int
        live_min_article: int
        desired_max_article: int
        desired_min_article: int

        current_min_article, current_max_article = self._dt.stat_group(group)
        if refresh:
            news = self.connect()
            _, _, live_min_article, live_max_article, _ = \
                news.group(group)
        else:
            live_min_article, live_max_article = \
                current_min_article, current_max_article
        desired_min_article = max(
            live_min_article,
            current_min_article - (abs(older) if refresh and older else 0)
        )
        desired_max_article = min(
            live_max_article,
            current_max_article + (abs(newer) if refresh and newer else 0)
        )
        if refresh and current_max_article < 1:
            desired_max_article = live_max_article
            desired_min_article = max(
                live_max_article - newer,
                current_min_article
            )
        updates = []
        if desired_min_article < current_min_article:
            updates.append(
                self.retrieve(
                    group,
                    desired_min_article,
                    current_min_article - 1
                )
            )
        if desired_max_article > current_max_article:
            updates.append(
                self.retrieve(
                    group,
                    current_max_article + 1
                    if current_max_article
                    else desired_min_article,
                    desired_max_article
                )
            )
        if updates:
            for batch in updates:
                total_updated = self._dt.update_messages(group, batch)
                logging.info(
                    "Updated %d values over %d headers",
                    total_updated,
                    len(batch)
                )
        current_min_article, current_max_article = self._dt.stat_group(group)
        if desired_min_article < current_min_article:
            logging.error(
                "Desired article #%d is less than actual minimum #%d",
                desired_min_article,
                current_min_article
            )
        if desired_max_article > current_max_article:
            logging.error(
                "Desired article #%d is greater than actual maximum #%d",
                desired_max_article,
                current_max_article
            )
        out_messages = self._dt.get_messages(group, **kwargs)
        # TODO: Consider returning an iterable of fetchmany() calls.
        return out_messages
