using System;
using BusinessObjects;
using Public;
using TrainingPeaksConnection;

namespace TestConsoleRunner
{
    internal class Program
    {
        private static void Main(string[] args)
        {
            var athlete = new Athlete();
            athlete.TPData = new TrainingPeaksAthleteData();
            athlete.TPData.LoginName = "jscbutler";
            athlete.TPData.LoginPassword = "xcelite1";
            athlete.TPData.AccountType = TrainingPeaksAthleteAccountTypes.SelfCoachedPremium;
            Console.Out.WriteLine("Starting connection to TrainingPeaks....");

            var conn = new TrainingPeaksClient();
            Console.Out.WriteLine("Initialised SOAP Client - starting to request Person Data");
            conn.GetAthleteData(athlete);
            Console.Out.WriteLine("Received Person Data - " + athlete.TPData.AthleteName + " ID:" +
                                  athlete.TPData.PersonID);
            Console.Out.WriteLine("Accesing last workout for " + athlete.Name);
            conn.GetLastWorkoutIn30Days(athlete);
            Console.In.ReadLine();
        }
    }
}