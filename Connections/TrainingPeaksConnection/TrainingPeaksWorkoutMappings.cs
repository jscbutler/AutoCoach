using System;
using BusinessObjects;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksWorkoutMappings
    {
        public static IWorkout MapCycleWorkout(Workout tpWorkout)
        {
            ICycleWorkout cycleWorkout = new CycleWorkout();
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
    }
}