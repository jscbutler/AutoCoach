using System;
using BusinessObjects;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksWorkoutMappings
    {
        public static AthleteAccountTypes AccountTypeMapping(TrainingPeaksAthleteAccountTypes accountType) => (AthleteAccountTypes)accountType;

        public static IWorkout CovertTPWorkoutToInternal(Workout tpWorkout)
        {
            IWorkout internalWorkout;
            switch (tpWorkout.WorkoutTypeDescription)
            {
                case "Swim":
                    {
                        internalWorkout = MapSwimWorkout(tpWorkout);
                        break;
                    }
                case "Cycle":
                    {
                        internalWorkout = MapCycleWorkout(tpWorkout);
                        break;
                    }
                case "Run":
                    {
                        internalWorkout = MapRunWorkout(tpWorkout);
                        break;
                    }
                case "Custom":
                    {
                        internalWorkout = MapCustomWorkout(tpWorkout);
                        break;
                    }
                default:
                    {
                        internalWorkout = new CycleWorkout();
                        break;
                    }
            }
            return internalWorkout;
        }
        public static IWorkout MapCycleWorkout(Workout tpWorkout)
        {
            ICycleWorkout cycleWorkout = new CycleWorkout();
            cycleWorkout.TPWorkoutID = tpWorkout.WorkoutId;
            cycleWorkout.CadenceAverage = tpWorkout.CadenceAverage;
            cycleWorkout.CadenceMaximum = tpWorkout.CadenceMaximum;
            cycleWorkout.PowerAverage = tpWorkout.PowerAverage;
            cycleWorkout.PowerMaximum = tpWorkout.PowerMaximum;
            cycleWorkout.StartDate = tpWorkout.WorkoutDay;
            cycleWorkout.StartTime = tpWorkout.StartTime;
            if (tpWorkout.TimeTotalInSeconds.HasValue)
                cycleWorkout.Duration = new TimeSpan(0, 0, (int) tpWorkout.TimeTotalInSeconds);
            cycleWorkout.DistanceInMeters = tpWorkout.DistanceInMeters;
            cycleWorkout.VelocityAverage = tpWorkout.VelocityAverage;
            cycleWorkout.VelocityMaximum = tpWorkout.VelocityMaximum;
            cycleWorkout.HeartRateAverage = tpWorkout.HeartRateAverage;
            cycleWorkout.HeartRateMaximum = tpWorkout.HeartRateMaximum;
            cycleWorkout.HeartRateMinimum = tpWorkout.HeartRateMinimum;

            return cycleWorkout;
        }

        public static IWorkout MapSwimWorkout(Workout tpWorkout)
        {
            ISwimWorkout swimWorkout = new SwimWorkout();
            swimWorkout.TPWorkoutID = tpWorkout.WorkoutId;
            swimWorkout.StartDate = tpWorkout.WorkoutDay;
            swimWorkout.StartTime = tpWorkout.StartTime;
            if (tpWorkout.TimeTotalInSeconds.HasValue)
                swimWorkout.Duration = new TimeSpan(0, 0, (int)tpWorkout.TimeTotalInSeconds);
            swimWorkout.DistanceInMeters = tpWorkout.DistanceInMeters;
            return swimWorkout;
        }

        public static IWorkout MapCustomWorkout(Workout tpWorkout)
        {
            ICustomWorkout customWorkout = new CustomWorkout();
            customWorkout.TPWorkoutID = tpWorkout.WorkoutId;
            customWorkout.StartDate = tpWorkout.WorkoutDay;
            customWorkout.StartTime = tpWorkout.StartTime;
            if (tpWorkout.TimeTotalInSeconds.HasValue)
                customWorkout.Duration = new TimeSpan(0, 0, (int)tpWorkout.TimeTotalInSeconds);
            return customWorkout;
        }
        public static IWorkout MapRunWorkout(Workout tpWorkout)
        {
            IRunWorkout runWorkout = new RunWorkout();
            runWorkout.CadenceAverage = tpWorkout.CadenceAverage;
            runWorkout.CadenceMaximum = tpWorkout.CadenceMaximum;
            runWorkout.PowerAverage = tpWorkout.PowerAverage;
            runWorkout.PowerMaximum = tpWorkout.PowerMaximum;
            runWorkout.StartDate = tpWorkout.WorkoutDay;
            runWorkout.StartTime = tpWorkout.StartTime;
            if (tpWorkout.TimeTotalInSeconds.HasValue)
                runWorkout.Duration = new TimeSpan(0, 0, (int)tpWorkout.TimeTotalInSeconds);
            runWorkout.DistanceInMeters = tpWorkout.DistanceInMeters;
            runWorkout.VelocityAverage = tpWorkout.VelocityAverage;
            runWorkout.VelocityMaximum = tpWorkout.VelocityMaximum;
            runWorkout.HeartRateAverage = tpWorkout.HeartRateAverage;
            runWorkout.HeartRateMaximum = tpWorkout.HeartRateMaximum;
            runWorkout.HeartRateMinimum = tpWorkout.HeartRateMinimum;
            runWorkout.TPWorkoutID = tpWorkout.WorkoutId;
            return runWorkout;
        }
    }
}