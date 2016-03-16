using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml;
using Public;

namespace BusinessObjects
{
    public class CustomWorkout : ICustomWorkout
    {
        public SportType SportType { get; }
        public double? TrainingStressScore { get; set; }
        public double? IntensityFactor { get; set; }
        public DateTime? StartDate { get; set; }
        public DateTime? StartTime { get; set; }
        public TimeSpan? Duration { get; set; }
        public double? DistanceInMeters { get; set; }
        public int TPWorkoutID   { get; set; }
        public XmlNode ExtendedPwXmlNode { get; set; }
        public object pwxData { get; set; }
    }
}
