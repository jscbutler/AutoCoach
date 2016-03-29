using System.Collections.Generic;
using Public;

namespace BusinessObjects
{
    public class Athlete : IAthlete
    {
        public Athlete()
        {
            BikeCadenceRanges = new List<ICadenceRange>(5);
            BikePowerEnergyRanges = new List<IEnergySystemRange>(6);
            BikeHeartRateEnergyRanges = new List<IEnergySystemRange>(6);
            // Can externally define these ranges later.
            BikeCadenceRanges.Add(new CadenceRange(0, 40, WorkoutCadenceFocus.None));
            BikeCadenceRanges.Add(new CadenceRange(40, 65, WorkoutCadenceFocus.Grinding));
            BikeCadenceRanges.Add(new CadenceRange(65, 80, WorkoutCadenceFocus.Climbing));
            BikeCadenceRanges.Add(new CadenceRange(80, 100, WorkoutCadenceFocus.Normal));
            BikeCadenceRanges.Add(new CadenceRange(100, 250, WorkoutCadenceFocus.Spinning));

            BikePowerEnergyRanges.Add(new EnergySystemRange(0, 55, WorkoutEnergySystemFocus.Zone1));
            BikePowerEnergyRanges.Add(new EnergySystemRange(55, 75, WorkoutEnergySystemFocus.Zone2));
            BikePowerEnergyRanges.Add(new EnergySystemRange(75, 90, WorkoutEnergySystemFocus.Zone3));
            BikePowerEnergyRanges.Add(new EnergySystemRange(90, 105, WorkoutEnergySystemFocus.Zone4));
            BikePowerEnergyRanges.Add(new EnergySystemRange(105, 120, WorkoutEnergySystemFocus.Zone5));
            BikePowerEnergyRanges.Add(new EnergySystemRange(120, 10000, WorkoutEnergySystemFocus.Zone6));

            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(0, 81, WorkoutEnergySystemFocus.Zone1));
            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(81, 89, WorkoutEnergySystemFocus.Zone2));
            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(90, 94, WorkoutEnergySystemFocus.Zone3));
            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(94, 103, WorkoutEnergySystemFocus.Zone4));
            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(103, 105, WorkoutEnergySystemFocus.Zone5));
            BikeHeartRateEnergyRanges.Add(new EnergySystemRange(105, 10000, WorkoutEnergySystemFocus.Zone6));

            // Run Pace
            //        Zone 1 Slower than 129% of FTP
            //Zone 2 114% to 129% of FTP
            //Zone 3 106% to 113% of FTP
            //Zone 4 99% to 105% of FTP
            //Zone 5a 97% to 100% of FTP
            //Zone 5b 90% to 96% of FTP
            //Zone 5c Faster than 90% of FTP           
        }

        public AthleteDiscipline Discipline { get; set; }
        public string Name { get; set; }
        public ITrainingPeaksAthleteData TPData { get; set; }
        public double FTBikePower { get; set; }
        public double FTRunSpeed { get; set; }
        public double CSSSwimSpeed { get; set; }
        public double WeightKilos { get; set; }
        public IList<ICadenceRange> BikeCadenceRanges { get; set; }
        public IList<IEnergySystemRange> BikePowerEnergyRanges { get; set; }
        public IList<IEnergySystemRange> BikeHeartRateEnergyRanges { get; set; }
    }
}