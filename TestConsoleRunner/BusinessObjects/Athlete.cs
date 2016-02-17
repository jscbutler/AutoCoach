using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Public;
namespace BusinessObjects
{
    public class Athlete : IAthlete
    {
        public AthleteDiscipline Discipline
        {
            get;set;
        }

        public string Name
        {
            get;set;
        }

        public ITrainingPeaksAthleteData TPData
        {       
            get;set;
        }
    }
}
