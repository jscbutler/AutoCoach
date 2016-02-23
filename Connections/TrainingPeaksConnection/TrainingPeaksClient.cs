using System;
using System.Collections.Generic;
using System.Linq;
using System.Xml;
using BusinessObjects;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection
{

    // IF = NP/FTP

    // TSS = ...x`
    /// <summary>
    ///     Normalized Power Calc.
    ///     1) starting at the 30 s mark, calculate a rolling 30 s average (of the preceeding time points, obviously).
    ///     2) raise all the values obtained in step #1 to the 4th power.
    ///     3) take the average of all of the values obtained in step #2. 
    ///     4) take the 4th root of the value obtained in step #3.
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
            System.Net.ServicePointManager.Expect100Continue = false;
            soapClient = new ServiceSoapClient("ServiceSoap");
        }

        public void GetAthleteData(IAthlete theAthlete)
        {
            var accessibleAthletes = soapClient.GetAccessibleAthletes(theAthlete.TPData.LoginName,
                theAthlete.TPData.LoginPassword, TrainingPeaksWorkoutMappings.AccountTypeMapping(theAthlete.TPData.AccountType));
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
            var workouts = GetAllWorkoutsInDateRange(athlete, DateTime.Now-TimeSpan.FromDays(30), DateTime.Now);
            return workouts[workouts.Count -2];
        }

        public List<IWorkout> GetWorkoutsInLast30Days(IAthlete athlete)
        {
            return GetAllWorkoutsInDateRange(athlete, DateTime.Now - TimeSpan.FromDays(30), DateTime.Now);
        }

        public List<IWorkout> GetAllWorkoutsInDateRange(IAthlete athlete, DateTime fromDate, DateTime toDate)
        {
            var workouts = soapClient.GetWorkoutsForAccessibleAthlete(athlete.TPData.LoginName,
                athlete.TPData.LoginPassword, athlete.TPData.PersonID, fromDate, toDate);
            var internalWorkoutList = new List<IWorkout>(100);
            internalWorkoutList.AddRange(workouts.Select(TrainingPeaksWorkoutMappings.CovertTPWorkoutToInternal));
            return internalWorkoutList;
        }

        public XmlNode GetExtendedWorkoutData(IAthlete athlete, IWorkout workout)
        {
            return workout.ExtendedPwXmlNode = soapClient.GetExtendedWorkoutDataForAccessibleAthlete(athlete.TPData.LoginName,
                athlete.TPData.LoginPassword, athlete.TPData.PersonID, workout.TPWorkoutID);
        }
    }
}