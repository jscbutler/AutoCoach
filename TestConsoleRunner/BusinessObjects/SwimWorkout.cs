using System;
using System.Xml;
using Public;

namespace BusinessObjects
{
    public class SwimWorkout : ISwimWorkout
    {
        public SportType SportType { get; }
        public double? TrainingStressScore { get; }
        public double? IntensityFactor { get; }
        public DateTime? StartDate { get; set; }
        public DateTime? StartTime { get; set; }
        public TimeSpan? Duration { get; set; }
        public double? DistanceInMeters { get; set; }
        public int TPWorkoutID { get; set; }
        public XmlNode ExtendedPwXmlNode { get; set; }
    }
}
