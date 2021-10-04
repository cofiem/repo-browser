import logging

from django.core.management.base import BaseCommand


class Logger:
    def __init__(self, log: logging.Logger = None, cmd: BaseCommand = None):
        self._cmd = cmd
        self._log = log
        self._prt = not cmd and not log

    def critical(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.CRITICAL):
            self._log.critical(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.ERROR(message))
        if self._prt:
            print(f"CRITICAL: {message}")

    def fatal(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.FATAL):
            self._log.fatal(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.ERROR(message))
        if self._prt:
            print(f"FATAL: {message}")

    def error(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.ERROR):
            self._log.error(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.ERROR(message))
        if self._prt:
            print(f"ERROR: {message}")

    def warning(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.WARNING):
            self._log.warning(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.WARNING(message))
        if self._prt:
            print(f"WARNING: {message}")

    def info(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.INFO):
            self._log.info(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.SUCCESS(message))
        if self._prt:
            print(f"INFO: {message}")

    def debug(self, message: str, *args, **kwargs):
        if self._log and self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(message, *args, **kwargs)
        if self._cmd:
            self._cmd.stdout.write(self._cmd.style.NOTICE(message))
        if self._prt:
            print(f"DEBUG: {message}")
