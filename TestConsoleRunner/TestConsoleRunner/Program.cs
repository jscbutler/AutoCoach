using System;
using System.Xml;
using BusinessObjects;
using Public;
using TrainingPeaksConnection;

namespace TestConsoleRunner
{
    internal class Program
    {
        private static void Main(string[] args)
        {
            var athlete = new Athlete
            {
                TPData = new TrainingPeaksAthleteData
                {
                    LoginName = "jscbutler",
                    LoginPassword = "xcelite1",
                    AccountType = TrainingPeaksAthleteAccountTypes.SelfCoachedPremium
                }
            };
            Console.Out.WriteLine("Starting connection to TrainingPeaks....");

            var conn = new TrainingPeaksClient();
            Console.Out.WriteLine("Initialised SOAP Client - starting to request Person Data");
            conn.GetAthleteData(athlete);
            Console.Out.WriteLine("Received Person Data - " + athlete.TPData.AthleteName + " ID:" +
                                  athlete.TPData.PersonID);
            Console.Out.WriteLine("Accesing last workout for " + athlete.TPData.AthleteName);
            var workout = conn.GetLastWorkoutIn30Days(athlete);
            XmlNode pwxData = conn.GetExtendedWorkoutData(athlete, workout);
            Console.In.ReadLine();
        }
    }
}