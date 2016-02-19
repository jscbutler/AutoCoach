using System;
using Public;

namespace BusinessObjects
{
    public class CycleWorkout : ICycleWorkout
    {
        public CycleWorkout()
        {
            SportType = SportType.Bike;
        }

        public SportType SportType { get; }
        public double? TrainingStressScore { get; }
        public double? IntensityFactor { get; }
        DateTime? IWorkout.StartDate { get; set; }
        DateTime? IWorkout.StartTime { get; set; }
        TimeSpan? IWorkout.Duration { get; set; }
        public int? CadenceAverage { get; set; }
        public int? CadenceMaximum { get; set; }
        public int? PowerAverage { get; set; }
        public int? PowerMaximum { get; set; }
        public double? VelocityMaximum { get; set; }
        public double? VelocityAverage { get; set; }
        public int? HeartRateAverage { get; set; }
        public int? HeartRateMaximum { get; set; }
        public int? HeartRateMinimum { get; set; }
        public double? DistanceInMeters { get; set; }
    }
}