from newsthing import Newsthing
import logging
import datetime
import argparse

parser = argparse.ArgumentParser(
    description="Slurp the news.",
    allow_abbrev=False
)
parser.add_argument("-f", "--db",
                    help="A database file",
                    required=True)
parser.add_argument("-s", "--server",
                    help="The news server",
                    required=True)
parser.add_argument("-p", "--port",
                    help="The news port",
                    type=int,
                    default=443)
parser.add_argument("group",
                    help="The newsgroup")
parser.add_argument("-b", "--batch-size",
                    help="The max. number of articles to retrieve in one batch",
                    type=int,
                    default=50000)
parser.add_argument("-c", "--repeat",
                    help="The max. number of batches to run",
                    dest="repeat_count",
                    type=int,
                    default=1)
parser.add_argument("-r", "--refresh",
                    help="Set to retrieve new messages from the server",
                    default=False,
                    action="store_true")
parser.add_argument("--debug",
                    help="Set the log level to DEBUG",
                    action="store_const",
                    dest="log_level",
                    const=logging.DEBUG)
parser.add_argument("-v", "--verbose",
                    help="Set the log level to INFO",
                    default=logging.WARN,
                    action="store_const",
                    dest="log_level",
                    const=logging.INFO)


def run_once(db, server, port, group, batch_size, refresh):
    news = Newsthing(db, server, port=port)
    messages = news.messages(group,
                             older=batch_size,
                             newer=batch_size,
                             refresh=refresh)
    print(f"Length of messages = {len(messages)}")
    print("\n".join([
        *map(lambda _: f"{_[0]} {_[1]} {_[2]} {_[3]}", messages[0:3]),
        "...",
        *map(lambda _: f"{_[0]} {_[1]} {_[2]} {_[3]}",
             messages[-3:]),
    ]))
    news.close()


if __name__ == '__main__':
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    for x in range(0, args.repeat_count):
        time_begin = datetime.datetime.now()
        run_once(
            db=args.db,
            server=args.server,
            port=args.port,
            group=args.group,
            batch_size=args.batch_size,
            refresh=args.refresh,
        )
        duration = datetime.datetime.now() - time_begin
        print(f"Batch duration: {duration}")
