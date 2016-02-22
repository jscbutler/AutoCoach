using System;
using System.Collections.Generic;
using System.Linq;
using BusinessObjects;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection
{
    //3) take the average of all of the values obtained in step #2. 

//4) take the 4th root of the value obtained in step #3. 

    // IF = NP/FTP

    // TSS = ...x`
    /// <summary>
    ///     Normalized Power Calc.
    ///     1) starting at the 30 s mark, calculate a rolling 30 s average (of the preceeding time points, obviously).
    ///     2) raise all the values obtained in step #1 to the 4th power.
    /// </summary>
    public class TrainingPeaksClient
    {
        private readonly ServiceSoap soapClient;

        public TrainingPeaksClient(ServiceSoap client)
        {
            soapClient = client;
        }

        public TrainingPeaksClient()
        {
            soapClient = new ServiceSoapClient("ServiceSoap");
        }

        public void GetAthleteData(IAthlete theAthlete)
        {
            var accessibleAthletes = soapClient.GetAccessibleAthletes(theAthlete.TPData.LoginName,
                theAthlete.TPData.LoginPassword, AccountTypeMapping(theAthlete.TPData.AccountType));
            if (accessibleAthletes.Length < 1)
                throw new Exception("No Athlete Data returned from GetAccessibleAthletes");
            if (accessibleAthletes.Length > 1)
                throw new Exception("More than 1 Athlete in profile for " + theAthlete.TPData.LoginName);
            var athlete = accessibleAthletes[0];
            theAthlete.TPData.AthleteName = athlete.FirstName + " " + athlete.LastName;
            theAthlete.TPData.PersonID = athlete.PersonId;
        }

        public IWorkout GetLastWorkoutIn30Days(IAthlete athlete)
        {
            var workouts = soapClient.GetWorkoutsForAccessibleAthlete(athlete.TPData.LoginName,
                athlete.TPData.LoginPassword, athlete.TPData.PersonID, DateTime.Today - TimeSpan.FromDays(30), DateTime.Today);
            var lastworkout = workouts.Last();
            return CovertTPWorkoutToInternal(lastworkout);
            var extendedWorkoutData = soapClient.GetExtendedWorkoutDataForAccessibleAthlete(athlete.TPData.LoginName,
                athlete.TPData.LoginPassword, athlete.TPData.PersonID, lastworkout.WorkoutId);
        }

        public List<IWorkout> GetRecentWorkouts(IAthlete athlete)
        {
            var workouts = soapClient.GetWorkoutsForAccessibleAthlete(athlete.TPData.LoginName,
                athlete.TPData.LoginPassword, athlete.TPData.PersonID, new DateTime(2016, 02, 01), DateTime.Today);
            var internalWorkoutList = new List<IWorkout>(100);
            internalWorkoutList.AddRange(workouts.Select(CovertTPWorkoutToInternal));
            return internalWorkoutList;
        }

        private IWorkout CovertTPWorkoutToInternal(Workout tpWorkout)
        {
            IWorkout internalWorkout = null;
            switch (tpWorkout.WorkoutTypeDescription)
            {
                case "Swim":
                {
                    break;
                }
                case "Cycle":
                {
                    internalWorkout = TrainingPeaksWorkoutMappings.MapCycleWorkout(tpWorkout);
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

        public static AthleteAccountTypes AccountTypeMapping(TrainingPeaksAthleteAccountTypes accountType)
        {
            return (AthleteAccountTypes) accountType;
        }
    }
}