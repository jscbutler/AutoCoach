using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Xml.Serialization;
using BusinessObjects;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksClient
    {
        private readonly ServiceSoap soapClient;

        public TrainingPeaksClient(ServiceSoap client)
        {
            soapClient = client;
        }

        public TrainingPeaksClient()
        {
            ServicePointManager.Expect100Continue = false;
            soapClient = new ServiceSoapClient("ServiceSoap");
        }

        public void GetAthleteData(IAthlete theAthlete)
        {
            var accessibleAthletes = soapClient.GetAccessibleAthletes(theAthlete.TPData.LoginName,
                theAthlete.TPData.LoginPassword,
                TrainingPeaksWorkoutMappings.AccountTypeMapping(theAthlete.TPData.AccountType));
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
            var workouts = GetAllWorkoutsInDateRange(athlete, DateTime.Now - TimeSpan.FromDays(30), DateTime.Now);
            return workouts[0];
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

        public pwx GetExtendedWorkoutData(IAthlete athlete, IWorkout workout)
        {
            var stm = new MemoryStream();
            var stw = new StreamWriter(stm);
            var xmlData =
                workout.ExtendedPwXmlNode =
                    soapClient.GetExtendedWorkoutDataForAccessibleAthlete(athlete.TPData.LoginName,
                        athlete.TPData.LoginPassword, athlete.TPData.PersonID, workout.TPWorkoutID);
            stw.Write(xmlData.OuterXml);
            stw.Flush();
            stm.Position = 0;
            var ser = new XmlSerializer(typeof (pwx));
            var pwxObj = ser.Deserialize(stm);
            workout.pwxData = pwxObj;
            return pwxObj as pwx;
        }
    }
}