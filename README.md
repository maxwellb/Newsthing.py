# Newsthing.py

Utility library and command line interface to sync newsgroup headers with a SQLite database file.

## Usage & Examples

```
$ python main.py -h
usage: main.py [-h] -f DB -s SERVER [-p PORT] [-b BATCH_SIZE] [-c REPEAT_COUNT] [-r] [--debug] [-v] group

Slurp the news.

positional arguments:
  group                 The newsgroup

optional arguments:
  -h, --help            show this help message and exit
  -f DB, --db DB        A database file
  -s SERVER, --server SERVER
                        The news server
  -p PORT, --port PORT  The news port
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        The max. number of articles to retrieve in one batch
  -c REPEAT_COUNT, --repeat REPEAT_COUNT
                        The max. number of batches to run
  -r, --refresh         Set to retrieve new messages from the server
  --debug               Set the log level to DEBUG
  -v, --verbose         Set the log level to INFO
```

Example: Load _comp.os.linux_ from a public server

```
$ python main.py -f news.db -s nntp.aioe.org -p 563 comp.os.linux -r
ERROR:root:Desired article #0 is less than actual minimum #1
Length of messages = 91
1 <i50214Fsp3rU1@mid.individual.net> 2020-12-29T06:52:20+00:00 Re: Linux in Crisis
2 <20201229083211.3148407c@nx-74205> 2020-12-29T08:32:11+01:00 Re: Linux in Crisis
3 <rsfdvm$1lld$30@gallifrey.nk.ca> 2020-12-29T14:20:38+00:00 Re: Linux in Crisis
...
89 <s1ua6u01kqh@news1.newsguy.com> 2021-03-05T22:09:34+00:00 Re: Questions about GParted for Data Recovery
90 <ubn84ghhg5egmijbhcih7afr0j62v1avjq@4ax.com> 2021-03-07T00:22:30-05:00 Re: Questions about GParted for Data Recovery
91 <o9pl4gt0irsll0khegn71o8tokvkehkb8i@4ax.com> 2021-03-11T23:10:53-05:00 Re: The Truth About Distros and Jim Jones
Batch duration: 0:00:02.111223

$ sqlite3 news.db
sqlite> select date, subject from nntp_aioe_org_comp_os_linux
   ...> order by date desc limit 10;
2021-03-11T23:10:53-05:00|Re: The Truth About Distros and Jim Jones
2021-03-07T00:22:30-05:00|Re: Questions about GParted for Data Recovery
2021-03-05T22:09:34+00:00|Re: Questions about GParted for Data Recovery
2021-03-05T17:21:03+01:00|Re: Questions about GParted for Data Recovery
2021-03-04T22:45:17-05:00|Re: Questions about GParted for Data Recovery
2021-03-04T15:10:36+01:00|Re: Questions about GParted for Data Recovery
2021-03-04T00:00:26-05:00|Re: Questions about GParted for Data Recovery
2021-03-03T03:56:20+00:00|Re: Pure Luck
2021-02-28T05:59:55+00:00|Re: Pure Luck
2021-02-28T00:20:43-05:00|Re: OpenSuse -vs- Centos/RHEL

$ python
Python 3.8.5 (default, Jan 27 2021, 15:41:15)
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from newsthing import Newsthing
>>> news = Newsthing("news.db", server="nntp.aioe.org", port=563)
>>> len(news.groups())
0
>>> len(news.groups(refresh=True))
43192
>>> news.groups()[0:5]
['1.test', '24hoursupport.helpdesk', 'a.b.boneless', 'a.bsu.religion', 'a.business.internet']
>>> news.messages("comp.os.linux", article=">= 89")
[
 (89, '<s1ua6u01kqh@news1.newsguy.com>', '2021-03-05T22:09:34+00:00', 'Re: Questions about GParted for Data Recovery', 'Charlie Gibbs <cgibbs@kltpzyxm.invalid>', 'NewsGuy.com', 'aioe.org!news.dns-netz.com!news.freedyn.net!newsreader4.netcologne.de!news.netcologne.de!peer03.ams1!peer.ams1.xlned.com!news.xlned.com!peer01.iad!feed-me.highwinds-media.com!news.highwinds-media.com!spln!extra.newsguy.com!newsp.newsguy.com!news1', 'comp.os.linux.misc,comp.os.linux', '<17cd25f1-91a6-4852-8031-af8138ce5d66n@googlegroups.com> <6lno3g54r5kski00mmb2pbbkb7o5onr2dt@4ax.com> <01f0e56c-8764-44e7-a212-81c85ce307b2n@googlegroups.com> <s1nh5e$phi$1@dont-email.me> <hoo04gde1lfve1rdsjpe49vppmuh6aeh37@4ax.com> <sb67hh-5hr.ln1@Telcontar.valinor> <ui934g1gt7qne7i3piov0tkqv0lmf36mkp@4ax.com>', None, None),
 (90, '<ubn84ghhg5egmijbhcih7afr0j62v1avjq@4ax.com>', '2021-03-07T00:22:30-05:00', 'Re: Questions about GParted for Data Recovery', '7EN <7en@r974x.org>', None, 'aioe.org!feeder5.feed.usenet.farm!feeder1.feed.usenet.farm!feed.usenet.farm!tr1.eu1.usenetexpress.com!feeder.usenetexpress.com!tr2.iad1.usenetexpress.com!border1.nntp.dca1.giganews.com!nntp.giganews.com!buffer1.nntp.dca1.giganews.com!buffer2.nntp.dca1.giganews.com!nntp.earthlink.com!news.earthlink.com.POSTED!not-for-mail', 'comp.os.linux.misc,comp.os.linux', '<17cd25f1-91a6-4852-8031-af8138ce5d66n@googlegroups.com> <6lno3g54r5kski00mmb2pbbkb7o5onr2dt@4ax.com> <01f0e56c-8764-44e7-a212-81c85ce307b2n@googlegroups.com> <s1nh5e$phi$1@dont-email.me> <hoo04gde1lfve1rdsjpe49vppmuh6aeh37@4ax.com> <sb67hh-5hr.ln1@Telcontar.valinor> <ui934g1gt7qne7i3piov0tkqv0lmf36mkp@4ax.com> <s1ua6u01kqh@news1.newsguy.com>', None, None),
 (91, '<o9pl4gt0irsll0khegn71o8tokvkehkb8i@4ax.com>', '2021-03-11T23:10:53-05:00', 'Re: The Truth About Distros and Jim Jones', '7EN <7en@r974x.org>', None, 'aioe.org!news.snarked.org!border2.nntp.dca1.giganews.com!nntp.giganews.com!buffer2.nntp.dca1.giganews.com!nntp.earthlink.com!news.earthlink.com.POSTED!not-for-mail', 'alt.os.linux,comp.os.linux,comp.os.linux.misc', '<s2e8gj01o1o@news2.newsguy.com>', None, None)
]
>>> [*map(lambda _: _[3], news.messages("comp.os.linux", subject="GParted*"))]
['Re: Questions about GParted for Data Recovery',
 'Re: Questions about GParted for Data Recovery',
 'Re: Questions about GParted for Data Recovery',
 'Re: Questions about GParted for Data Recovery',
 'Re: Questions about GParted for Data Recovery',
 'Re: Questions about GParted for Data Recovery']
```

