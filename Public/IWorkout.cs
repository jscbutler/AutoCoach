﻿using System;
using System.Xml;

namespace Public
{
    public interface IWorkout
    {
        SportType SportType { get; }
        double? TrainingStressScore { get; }
        double? IntensityFactor { get; }
        DateTime? StartDate { get; set; }
        DateTime? StartTime { get; set; }
        TimeSpan? Duration { get; set; }
        double? DistanceInMeters { get; set; }
        int TPWorkoutID { get; set; }
        XmlNode ExtendedPwXmlNode { get; set; }
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