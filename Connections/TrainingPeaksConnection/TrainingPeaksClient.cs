using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Public;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksClient
    {

        TrainingPeaksServiceReference.ServiceSoapClient soapClient;
        public TrainingPeaksClient()
        {
            soapClient = new TrainingPeaksServiceReference.ServiceSoapClient("ServiceSoap");
        }

        public void GetAthleteData(IAthlete theAthlete)
        {
            var accessibleAthletes = soapClient.GetAccessibleAthletes(theAthlete.TPData.LoginName, theAthlete.TPData.LoginPassword, AccountTypeMapping(theAthlete.TPData.AccountType));
            if (accessibleAthletes.Length > 1)
                throw new Exception("More than 1 Athlete in profile for " + theAthlete.TPData.LoginName);
            var athlete = accessibleAthletes[0];
            TrainingPeaksAthleteData tpAthleteData = new TrainingPeaksAthleteData();
            tpAthleteData.AthleteName = athlete.FirstName + " " + athlete.LastName;
            tpAthleteData.PersonID = athlete.PersonId;
        }

        public void GetLastWorkout (IAthlete athlete)
        {
            var workouts = soapClient.GetWorkoutsForAccessibleAthlete(athlete.TPData.LoginName, athlete.TPData.LoginPassword, athlete.TPData.PersonID, new DateTime(2016, 01, 01), DateTime.Today);
            var lastworkout = workouts.Last();
            var extendedWorkoutData = soapClient.GetExtendedWorkoutDataForAccessibleAthlete(athlete.TPData.LoginName, athlete.TPData.LoginPassword, athlete.TPData.PersonID, lastworkout.WorkoutId);
        }

        TrainingPeaksServiceReference.AthleteAccountTypes AccountTypeMapping (TrainingPeaksAthleteAccountTypes accountType)
        {
            return (TrainingPeaksServiceReference.AthleteAccountTypes)accountType;
        }
    }
}
