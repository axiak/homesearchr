import datetime

__all__ = ('ZONES',)

ZONES = {
    'EDT': datetime.timedelta(hours=-4),
    'EST': datetime.timedelta(hours=-5),
    'ADT': datetime.timedelta(hours=-3),
    'AKDT': datetime.timedelta(hours=-8),
    'AKST': datetime.timedelta(hours=-9),
    'AST': datetime.timedelta(hours=-4),
    'CDT': datetime.timedelta(hours=-5),
    'CST': datetime.timedelta(hours=-6),
    'GMT': datetime.timedelta(hours=0),
    'UTC': datetime.timedelta(hours=0),
    'MDT': datetime.timedelta(hours=-6),
    'MST': datetime.timedelta(hours=-7),
    'NDT': datetime.timedelta(hours=-2, minutes=-30),
    'PDT': datetime.timedelta(hours=-7),
    'PST': datetime.timedelta(hours=-8),
    }
