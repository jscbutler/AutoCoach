using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrainingPeaksConnection;
using Public;
using BusinessObjects;

namespace TestConsoleRunner
{
    class Program
    {
        static void Main(string[] args)
        {
            Athlete athlete = new Athlete();
            athlete.TPData = new TrainingPeaksAthleteData();
            athlete.TPData.LoginName = "jscbutler";
            athlete.TPData.LoginPassword = "xcelite1";
            athlete.TPData.AccountType = TrainingPeaksAthleteAccountTypes.SelfCoachedPremium;

            Console.Out.WriteLine("Starting connection to TrainingPeaks....");

            TrainingPeaksClient conn = new TrainingPeaksClient();
            Console.Out.WriteLine("Initialised SOAP Client - starting to request Person Data");
            conn.GetAthleteData(athlete);
            Console.Out.WriteLine("Received Person Data - " + athlete.TPData.AthleteName + " ID:" + athlete.TPData.PersonID);
            Console.Out.WriteLine("Accesing last workout for " + athlete.Name);
            conn.GetLastWorkout(athlete);
            Console.In.ReadLine();
        }
    }
}
