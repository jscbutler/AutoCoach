using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Linq;
using System.Xml.Serialization;
using Public;

namespace BusinessObjects
{
    [Serializable]
    public class Activity
    {
        public Activity()
        { }
        public Activity(SportType sport, DateTime startTime, TimeSpan duration)
        {
            SportType = sport;
            StartTime = startTime;
            Duration = duration;
        }

        public SportType SportType { get; set; }
        public DateTime StartTime { get; set; }
        private TimeSpan _duration;

        [XmlIgnore]
        public TimeSpan Duration
        {
            get { return _duration; }
            set { _duration = value; }
        }

        // Pretend property for serialization
        [XmlElement("Duration")]
        public long DurationTicks
        {
            get { return _duration.Ticks; }
            set { _duration = new TimeSpan(value); }
        }
    }

    [Serializable]
    public sealed class TrainingCalendarDay
    {
        [XmlElement("Activities")]
        public List<Activity> ActivityList { get; set; }

        public TrainingCalendarDay()
        {
            ActivityList = new List<Activity>(5);
        }

        public TrainingCalendarDay(DateTime myDay)
        {
            ActivityList =new List<Activity>(5);
            Date = myDay;
        }

        [XmlAttribute]
        public DateTime Date { get; set; }

        [XmlIgnore]
        public TimeSpan TotalTrainingTime
        {
            get
            {
                return ActivityList.Aggregate(TimeSpan.Zero,
                    (sumSoFar, nextMyObject) => sumSoFar + nextMyObject.Duration);
            }
        }

        public void AddActivity(Activity activity)
        {
            if (activity.StartTime.Date != Date.Date)
                throw new ArgumentOutOfRangeException("Cannot add activity for date " + activity.StartTime.Date +
                                                      " to a training day of date " + Date.Date);
            ActivityList.Add(activity);
            
        }
    }

   
    public class TrainingCalendarWeek
    {
        public TrainingCalendarWeek()
        {
        }

        public TrainingCalendarWeek(DateTime startDate, TrainingPhase phase, double weekTssTarget,
            TimeSpan weekHoursTarget)
        {
            if (startDate.DayOfWeek != DayOfWeek.Monday)
            {
                throw new ArgumentOutOfRangeException("First Day of week must be Monday");
            }
            Phase = phase;
            FirstDate = startDate;
            LastDate = FirstDate + TimeSpan.FromDays(7);
            DaysOfWeek = new List<TrainingCalendarDay>(7);
            for (var i = 0; i < 7; i++)
            {
                DaysOfWeek.Add(new TrainingCalendarDay {Date = startDate + TimeSpan.FromDays(i)});
            }
            WeekTssTarget = weekTssTarget;
            _weekHoursTarget = weekHoursTarget;
        }

        [XmlElement("DaysOfWeek")]
        //[XmlArrayItem (typeof(TrainingCalendarDay))]
        public List<TrainingCalendarDay> DaysOfWeek { get; set; }


        [XmlAttribute("FirstDateInWeek")]
        public DateTime FirstDate { get; set; }

        [XmlAttribute("LastDateInWeek")]
        public DateTime LastDate { get; set; }

        [XmlAttribute("TrainingPhase")]
        public TrainingPhase Phase { get; set; }

        [XmlAttribute("WeeklyTSSTarget")]
        public double WeekTssTarget { get; set; }

        private TimeSpan _weekHoursTarget;

        [XmlIgnore]
        public TimeSpan WeekHoursTarget
        {
            get { return _weekHoursTarget; }
            set { _weekHoursTarget = value; }
        }

        // Pretend property for serialization
        [XmlElement("WeekHoursTarget")]
        public long WeekHoursTargetTicks
        {
            get { return _weekHoursTarget.Ticks; }
            set { _weekHoursTarget = new TimeSpan(value); }
        }

        public void AddDay(TrainingCalendarDay day)
        {
            if ((day.Date < FirstDate) || (day.Date > LastDate))
                throw new ArgumentOutOfRangeException(" Day added " + day.Date +
                                                      " is out of range for this week FirstDate " + FirstDate);
            var dayIndex = (int) day.Date.DayOfWeek - 1;
            DaysOfWeek[dayIndex] = day;
        }

        public TimeSpan TotalTrainingTime()
        {
            return DaysOfWeek.Aggregate(TimeSpan.Zero, (sumSoFar, nextValue) => sumSoFar + nextValue.TotalTrainingTime);
        }
    }
}