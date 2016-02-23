using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml;
using Public;

namespace BusinessObjects
{
    public class RunWorkout: IRunWorkout
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
        public int? CadenceAverage { get; set; }
        public int? CadenceMaximum { get; set; }
        public int? PowerAverage { get; set; }
        public int? PowerMaximum { get; set; }
        public double? VelocityMaximum { get; set; }
        public double? VelocityAverage { get; set; }
        public int? HeartRateAverage { get; set; }
        public int? HeartRateMaximum { get; set; }
        public int? HeartRateMinimum { get; set; }
    }
}
