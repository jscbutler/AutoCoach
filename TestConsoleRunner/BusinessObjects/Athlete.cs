using Public;

namespace BusinessObjects
{
    public class Athlete : IAthlete
    {
        public AthleteDiscipline Discipline { get; set; }
        public string Name { get; set; }
        public ITrainingPeaksAthleteData TPData { get; set; }
        public double FTBikePower { get; set; }
        public double FTRunSpeed { get; set; }
        public double CSSSwimSpeed { get; set; }
        public double WeightKilos { get; set; }
    }
}