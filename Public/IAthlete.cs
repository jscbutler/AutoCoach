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
    }

    public interface ISportData
    {
        SportType Type { get; }
    }
}