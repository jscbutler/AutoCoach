
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
        ITrainingPeaksAthleteData TPData { get; }

    };

    public interface ISportData
    {
        SportType Type { get; }


    }

     


    public interface ITrainingPeaksAthleteData
    {
        string LoginName { get; set; }
        string LoginPassword { get; set; }
        TrainingPeaksAthleteAccountTypes AccountType { get; set; }
        int PersonID { get; }
        string AthleteName { get; }

    }


    public enum TrainingPeaksAthleteAccountTypes
    {

        /// <remarks/>
        CoachedPremium = 1,

        /// <remarks/>
        SelfCoachedPremium = 2,

        /// <remarks/>
        SharedSelfCoachedPremium = 4,

        /// <remarks/>
        SharedCoachedPremium = 8,

        /// <remarks/>
        CoachedFree = 16,

        /// <remarks/>
        SharedFree = 32,

        /// <remarks/>
        Plan = 64,
    }


}
