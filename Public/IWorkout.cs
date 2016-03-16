using System;
using System.Runtime.InteropServices;
using System.Xml;

namespace Public
{
    public enum WorkoutEnergySystemFocus
    {
        Zone1=0,
        Zone2,
        Zone3,
        Zone4,
        Zone5,
        Zone6,
    }

    public enum WorkoutCadenceFocus
    {
        None=0,
        Grinding,
        Climbing,
        Normal,
        Spinning
    }

    public interface IWorkout
    {
        SportType SportType { get; }
        double? TrainingStressScore { get; set; }
        double? IntensityFactor { get; set; }
        DateTime? StartDate { get; set; }
        DateTime? StartTime { get; set; }
        TimeSpan? Duration { get; set; }
        double? DistanceInMeters { get; set; }
        int TPWorkoutID { get; set; }
        XmlNode ExtendedPwXmlNode { get; set; }
        object pwxData { get; set; }
    }

    public interface ICycleWorkout : IWorkout
    {
        int? CadenceAverage { get; set; }
        int? CadenceMaximum { get; set; }
        int? PowerAverage { get; set; }
        int? PowerMaximum { get; set; }
        double? VelocityMaximum { get; set; }
        double? VelocityAverage { get; set; }
        int? HeartRateAverage { get; set; }
        int? HeartRateMaximum { get; set; }
        int? HeartRateMinimum { get; set; }
        int? NormalizedPower { get; set; }
    }

    public interface ISwimWorkout : IWorkout
    {
        
    }

    public interface IRunWorkout : IWorkout
    {
        int? CadenceAverage { get; set; }
        int? CadenceMaximum { get; set; }
        int? PowerAverage { get; set; }
        int? PowerMaximum { get; set; }
        double? VelocityMaximum { get; set; }
        double? VelocityAverage { get; set; }
        int? HeartRateAverage { get; set; }
        int? HeartRateMaximum { get; set; }
        int? HeartRateMinimum { get; set; } 
    }

    public interface ICustomWorkout : IWorkout
    {
        
    }

    
  
}