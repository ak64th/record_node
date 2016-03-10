(function(root, Backbone){
  app = root.app || {};

  app.Option = Backbone.Model.extend({});

  app.Question = Backbone.Model.extend({
    defaults: {
      "selected": [],
      "timeout":  false,
      "answered": false
    },
    isCorrect: function(){
      if (!this.get('answered')) return false;
      var answer = this.get('answer');
      var selected = _(this.get('selected')).pluck('id');
      if(answer && selected && answer.length === selected.length){
        return _.difference(answer, selected).length === 0;
      }
      return false;
    },
    getAnswerCodes: function(){
      var answer = this.get('answer'),
          options = this.get('options');
      return _.map(answer, function(id){
        return options.get(id).get('code');
      });
    }
  });

  app.OptionCollection = Backbone.Collection.extend({model: app.Option});

  app.QuestionCollection = Backbone.Collection.extend({
    model: app.Question,
    totalPoints: function(questionPoints){
      var totalPoints = 0;
      this.each(function(model){
        if (model.get('answered') && model.isCorrect()){
          totalPoints += questionPoints[model.get('type')];
        }
      }, this);
      return totalPoints;
    }
  });

  root.app = app;
  return app;
})(window, Backbone);
