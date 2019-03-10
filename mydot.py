#!/usr/bin/env python
import os
import sys
import yaml
import click
import logging
import colorama
import copy
import git
import socket
import shutil
from pathlib import Path

LOGGING_STRING='[%(levelname)s] %(message)s'

logger = logging.getLogger(__name__)

dotdir = None

class MyDot(object):
    path = None
    repo = None
    uid = None


    _config_filename="config.yaml"

    def __init__(self, path):
        self.path = Path(path)
        self.uid = socket.gethostname()

    def repostatus(self):
        behind = self.repo.iter_commits('master..origin/master')
        ahead = self.repo.iter_commits('origin/master..master')
        num_behind=sum(1 for c in behind)
        num_ahead=sum(1 for c in ahead)
        if num_behind:
            return '{} commits behind origin'.format(num_behind)
        elif num_ahead:
            return '{} commits ahead origin'.format(num_ahead)
        return 'in sync with origin'

    def load_config(self):
        config_file = self.path / self._config_filename
        logger.debug('Loading config: {}'.format(config_file.as_posix()))
        if not config_file.exists():
            logger.debug('Creating new config file')
            config = {
                    'host': [ self.uid ]
                    }
            with config_file.open('w') as outfile:
                yaml.dump(config, outfile, default_flow_style=False)
            self.add(config_file.as_posix(), 'Added new config file')

    def behind(self):
        commits_behind = self.repo.iter_commits('master..origin/master')
        return sum(1 for c in commits_behind)

    def ahead(self):
        commits_ahead = repo.iter_commits('origin/master..master')
        return sum(1 for c in commits_ahead)


class ColorLogFormater(logging.Formatter):
    COLOR = {
            logging.ERROR: colorama.Fore.RED,
            logging.CRITICAL: colorama.Fore.RED,
            logging.WARNING: colorama.Fore.YELLOW,
            logging.DEBUG: colorama.Fore.BLUE
            }
    STYLE = {
            logging.ERROR: colorama.Style.BRIGHT,
            logging.CRITICAL: colorama.Style.BRIGHT,
            logging.WARNING: colorama.Style.BRIGHT,
            logging.DEBUG:  colorama.Style.BRIGHT
            }

    def format(self, record, *args, **kwargs):
        theRecord = copy.copy(record)
        if theRecord.levelno in self.COLOR:
            theRecord.levelname = "{color}{style}{level}{reset}".format(
                    color=self.COLOR[theRecord.levelno],
                    style=self.STYLE[theRecord.levelno],
                    level=record.levelname,
                    reset=colorama.Style.RESET_ALL)
        return super(ColorLogFormater, self).format(theRecord, *args, **kwargs)


def format_logger(loglevel, nocolor=False):
    logger.setLevel(logging.getLevelName(loglevel))
    if nocolor:
        formatter = logging.Formatter(LOGGING_STRING)
    else:
        formatter = ColorLogFormater(LOGGING_STRING)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.getLevelName(loglevel))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


@click.group()
@click.option('--path', type=click.Path(), default="{}/.dotfiles".format(Path.home()), help="set root of dotdir git folder [default = ~/.mydot]")
@click.option('--loglevel', type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NOTSET"]), default="WARNING", help="Set the logging level")
@click.pass_context
def main(ctx, path, loglevel):
    global dotdir
    format_logger(loglevel)
    logger.debug('Starting..')
    dotdir = MyDot(os.path.abspath(path))
    if ctx.invoked_subcommand != 'init':
        if dotdir.path.exists() and dotdir.path.is_dir():
            logger.debug('Loading git repo')
            try:
                dotdir.repo = git.Repo(dotdir.path.as_posix())
            except git.InvalidGitRepositoryError as e:
                logger.critical('Invalit git repository: {}'.format(e))
                sys.exit(1)
        else:
            if not dotdir.path.exists():
                logger.critical('Local repo dont exists {}, you might want to run init'.format(dotdir.path.as_posix()))
                sys.exit(1)
            logger.critical('{} is not a directory'.format(dotdir.path.as_posix()))
            sys.exit(1)
    dotdir.load_config()
    #ctx.obj['DOTDIR'] = dotdir

@main.command()
@click.pass_context
def status(ctx):
    """ Invoke git repo commands..."""
    global dotdir
    print('Repo description: {}'.format(dotdir.repo.description))
    print('Last commit for repo is {}.'.format(str(dotdir.repo.head.commit.hexsha)))
    commits_behind = dotdir.repo.iter_commits('master..origin/master')
    commits_ahead = dotdir.repo.iter_commits('origin/master..master')
    print(sum(1 for c in commits_behind))
    print(sum(1 for c in commits_ahead))
    for remote in dotdir.repo.remotes:
        print('    Remote named "{}" with URL "{}"'.format(remote, remote.url))
    if dotdir.repo.is_dirty():
        print('\n{}{}Changed files{}:'.format(colorama.Style.BRIGHT, colorama.Fore.YELLOW, colorama.Style.RESET_ALL))
        for item in dotdir.repo.index.diff(None):
            print('  * {}'.format(item.a_path))
        #TODO: List all deleted files
    if dotdir.repo.untracked_files:
        print('\n{}{}Untracked files{}:'.format(colorama.Style.BRIGHT, colorama.Fore.YELLOW, colorama.Style.RESET_ALL))
        for f in dotdir.repo.untracked_files:
            print('  * {}'.format(f))

    if not dotdir.repo.is_dirty() and not dotdir.untracked_files:
        print('\n{}{}Status OK!{}'.format(colorama.Style.BRIGHT, colorama.Fore.GREEN, colorama.Style.RESET_ALL))

@main.command()
@click.argument('fname')
@click.pass_context
def remove(ctx, fname):
    """Remove file from dotdir, it will remove the link and move the file from the repository"""
    global dotdir
    fname = os.path.abspath(fname)
    if not fname.startswith(dotdir.path.as_posix()):
        logger.error('{} is not in your repository [{}]'.format(fname, dotdir.path.as_posix()))
        sys.exit(1)

    destfile = '{home}/{path}'.format(
        home=Path.home().as_posix(),
        path=fname.replace(dotdir.path.as_posix()+'/'+dotdir.uid+'/', '')
        )


    if Path(destfile).is_symlink():
        if not os.readlink(destfile) == fname:
            logger.error("The target symlink is pointing to wrong file [{}]".format(os.readlink(destfile)))
            sys.exit(1)
    else:
        logger.error("The target {} is not a symlink".format(destfile))
        sys.exit(1)

    logger.debug('Unlinking {}'.format(destfile))
    os.unlink(destfile)
    logger.debug('Copy {} > {}'.format(fname, destfile))
    shutil.copy(fname, destfile)
    logger.debug('Removing {} from repo'.format(fname))
    gitfile=fname.replace(dotdir.path.as_posix()+'/', '')
    if gitfile in dotdir.repo.untracked_files:
        logger.debug('{} is not commited yet'.format(fname))
        if Path(fname).is_symlink():
            logger.debug('{} is a symlink, unlinking'.format(fname))
            os.unlink(fname)
        else:
            logger.debug('removing {}'.format(fname))
            os.remove(fname)
    else:
        logger.debug('{} is commited, removing file'.format(gitfile))
        dotdir.repo.index.remove([gitfile],working_tree = True)



@main.command()
@click.argument('url')
@click.pass_context
def init(ctx, url):
    """Init a local repository with URL as remotei origin"""
    #dotdir = ctx.obj['DOTDIR']
    if dotdir.path.exists():
        logger.critical('Can not init local repo when {} already exists'.format(dotdir.path.as_posix()))
        sys.exit(1)
    logger.info('Creating local repo: {}'.format(dotdir.path.as_posix()))
    repo = git.Repo.init(dotdir.path.as_posix())
    logger.info('Adding remote origin: {}'.format(url))
    origin = repo.create_remote('origin', url)
    logger.info('Fetching origin')
    origin.fetch()
    logger.info('Remote pull')
    origin.pull(origin.refs[0].remote_head)
    dotdir.load_config()


@main.command()
@click.argument('source')
@click.pass_context
def add(ctx, source):
    """Add a file to managed dotfile"""
    global dotdir
    source = os.path.abspath(source)
    """Check if Source is located in home directory and not in dotdir"""
    logger.debug('Checking if {} is valid to add'.format(source))
    if not source.startswith(str(Path.home())):
        logger.critical('You can only add files from your home directory')
        sys.exit(1)
    if source.startswith(str(dotdir.path.as_posix())):
        logger.critical('You can not add files from your local mydot git repo')
        sys.exit(1)

    destfile = '{repo}/{uid}{path}'.format(
        repo=dotdir.path.as_posix(),
        uid=dotdir.uid,
        path=source.replace(Path.home().as_posix(), '')
        )
    if os.path.isfile(destfile):
        logger.error("There's already a file in ~{}".format(destfile.replace(Path.home().as_posix(), "")))
        sys.exit(1)
    if os.path.isdir(destfile):
        logger.error("~{} is an existing directory".format(destfile.replace(Path.home().as_posix(), "")))
        sys.exit(1)
    
    if os.path.exists(os.path.dirname(destfile)) and os.path.isfile(os.path.dirname(destfile)):
        logger.error('Destination directory [~{}] is a file'.format(os.path.dirname(destfile)))
        sys.exit(1)
    elif not os.path.exists(os.path.dirname(destfile)):
        logger.debug('Creating directory ~{}'.format(os.path.dirname(destfile)))
        os.makedirs(os.path.dirname(destfile))
    
    logger.debug('Moving file to repo')
    os.rename(source, destfile)
    logger.debug('Creating symlink')
    os.symlink(destfile, source)

if __name__ == "__main__":
    sys.argv[0] = "mydot"
    main(obj={})
