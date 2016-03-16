namespace Public
{
    public enum AthleteDiscipline
    {
        Runner,
        Cyclist,
        Swimmer,
        Triathlete
    }

    public enum SportType
    {
        Swim,
        Bike,
        Run,
        Strength
    }

    public interface IAthlete
    {
        string Name { get; }
        AthleteDiscipline Discipline { get; }
        ITrainingPeaksAthleteData TPData { get; set; }
        double FTBikePower { get; set; }
        double FTRunSpeed { get; set; }
        double CSSSwimSpeed { get; set; }
        double WeightKilos { get; set; }
    }

    public interface ISportData
    {
        SportType Type { get; }
    }
}