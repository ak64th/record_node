(function(root){
  app = root.app || {};

  app.QUESTION_TYPE = {
    MULTI: 'multi',
    SINGLE: 'single'
  };

  app.QUIZ_TYPE = {
    ORDINARY: 'ordinary',
    TIME_LIMIT: 'time_limit',
    CHALLENGE: 'challenge'
  };

  app.DOWNLOAD_TIMEOUT = 3000;
  app.DOWNLOAD_TRIGGER = 30; // download more if questions are less than this value, only for time limit and challenge mode

  root.app = app;
  return app;
})(window);

(function(root, $, _, Backbone) {
  app = root.app || {};

  app.ApplicationView = Backbone.View.extend({
    el: $('#app_container'),
    dataRoot: '/data/',
    apiRoot: '/api/',
    initialize: function(options) {
      this.game_code = options.game_code;
      this.gameDataRoot = this.dataRoot + this.game_code + '/';
      this.quizConfig = options.config;
    },
    run: function() {
      var errorView;
      var used = parseInt(localStorage.getItem(this.game_code + '_count')) || 0,
        max = parseInt(this.quizConfig.max_chances);
      if (used > max) {
        errorView = new app.RejectionNoMoreChanceView();
      } else {
        var now = new Date(),
          start_at = new Date(this.quizConfig.start_at),
          end_at = new Date(this.quizConfig.end_at);
        if (now < start_at) {
          errorView = new app.RejectionTooEarlyView();
        } else if (now > end_at) {
          errorView = new app.RejectionTooLateView();
        }
      };
      if (errorView) {
        this.loadView(errorView);
      } else {
        this.prepareQuiz();
      }
    },
    rerun: function(){
      delete this.run_id;
      delete this.uid;
      this.run();
    },
    loadView: function(view) {
      this.view && (this.view.close ? this.view.close() : this.view.remove());
      this.view = view;
      this.$el.append(this.view.render().el);
    },
    loadStyle: function(){
      var style, quizType = this.quizConfig['type'];
      switch (quizType) {
        case app.QUIZ_TYPE.ORDINARY:
          style = 'theme1/css/main.css';
          break;
        case app.QUIZ_TYPE.TIME_LIMIT:
          style = 'theme2/css/main.css';
          break;
        case app.QUIZ_TYPE.CHALLENGE:
          style = 'theme3/css/main.css';
          break;
        default:
          throw new Error('Unknown Quiz Type');
      }
      $('head').append('<link rel="stylesheet" type="text/css" href="' + style + '"/>');
    },
    prepareQuiz: function() {
      var view = new app.WelcomeView({
        content: this.quizConfig.welcome,
        infoFields: this.quizConfig.info_fields,
        quizId: this.quizConfig.id
      });
      this.listenToOnce(view, 'startQuiz', this.gatherUserInfo);
      this.loadView(view);
    },
    gatherUserInfo: function(args){
      var params = {}, storageKey;
      if(_.size(args) > 0){
        var userinfo = JSON.stringify(_.object(args));
        var hash = mmh3(userinfo);
        var storageKey = this.game_code + '_uid_' + hash;
        var uid = localStorage.getItem(storageKey);
        if ( !uid ){
          params['hash'] = hash;
          params['userinfo'] = userinfo;
        } else {
          params['uid'] = uid;
        }
      }
      $.ajax({
        url: this.apiRoot + 'start/' + this.quizConfig.id,
        data: params,
        method: 'POST'
      }).done(_.bind(function(data){
        this.run_id = data['run_id'];
        if(!!storageKey){
          this.uid = data['uid'];
          localStorage.setItem(storageKey, data['uid']);
        }
        this.startQuiz();
      }, this));
    },
    startQuiz: function() {
      console.log(this.uid, this.run_id);
      var ViewClass, quizType = this.quizConfig['type'];
      var style = '';
      switch (quizType) {
        case app.QUIZ_TYPE.ORDINARY:
          ViewClass = app.OrdinaryQuizView;
          break;
        case app.QUIZ_TYPE.TIME_LIMIT:
          ViewClass = app.TimeLimitQuizView;
          break;
        case app.QUIZ_TYPE.CHALLENGE:
          ViewClass = app.ChallengeQuizView;
          break;
        default:
          throw new Error('Unknown Quiz Type');
      }
      var view = new ViewClass({
        config: this.quizConfig,
        gameDataRoot: this.gameDataRoot
      });
      var used = parseInt(localStorage.getItem(this.game_code + '_count')) || 0;
      localStorage.setItem(this.game_code + '_count', used + 1);
      this.listenToOnce(view, 'finishQuiz', this.finishQuiz);
      this.loadView(view);
    },
    finishQuiz: function(points) {
      console.log("结束，得到" + points + '分');
      var result = {'points': points};
      var data =  { 'score': points,'run_id': this.uid };
      if (!!this.uid) data['uid'] = this.uid
      $.ajax({
        url: this.apiRoot + 'end/' + this.quizConfig.id,
        data: data,
        method: 'POST'
      }).done(_.bind(function(data){
        console.log(data);
        result['rank'] = data['rank'];
        result['bestPoints'] = data['best_score'];
        result['bestRank'] = data['best_rank'];
        var view = new app.RankView({'result': result});
        this.listenToOnce(view, 'rerun', this.rerun);
        this.loadView(view);
      }, this));
    }
  });

  // mumurhash3 function from github.com/garycourt/murmurhash-js
  function mmh3(key, seed) {
    var remainder, bytes, h1, h1b, c1, c1b, c2, c2b, k1, i;
    remainder = key.length & 3; // key.length % 4
    bytes = key.length - remainder;
    h1 = seed;
    c1 = 0xcc9e2d51;
    c2 = 0x1b873593;
    i = 0;
    while (i < bytes) {
      k1 =
        ((key.charCodeAt(i) & 0xff)) |
        ((key.charCodeAt(++i) & 0xff) << 8) |
        ((key.charCodeAt(++i) & 0xff) << 16) |
        ((key.charCodeAt(++i) & 0xff) << 24);
      ++i;
      k1 = ((((k1 & 0xffff) * c1) + ((((k1 >>> 16) * c1) & 0xffff) << 16))) & 0xffffffff;
      k1 = (k1 << 15) | (k1 >>> 17);
      k1 = ((((k1 & 0xffff) * c2) + ((((k1 >>> 16) * c2) & 0xffff) << 16))) & 0xffffffff;
      h1 ^= k1;
      h1 = (h1 << 13) | (h1 >>> 19);
      h1b = ((((h1 & 0xffff) * 5) + ((((h1 >>> 16) * 5) & 0xffff) << 16))) & 0xffffffff;
      h1 = (((h1b & 0xffff) + 0x6b64) + ((((h1b >>> 16) + 0xe654) & 0xffff) << 16));
    }
    k1 = 0;
    switch (remainder) {
      case 3:
        k1 ^= (key.charCodeAt(i + 2) & 0xff) << 16;
      case 2:
        k1 ^= (key.charCodeAt(i + 1) & 0xff) << 8;
      case 1:
        k1 ^= (key.charCodeAt(i) & 0xff);
        k1 = (((k1 & 0xffff) * c1) + ((((k1 >>> 16) * c1) & 0xffff) << 16)) & 0xffffffff;
        k1 = (k1 << 15) | (k1 >>> 17);
        k1 = (((k1 & 0xffff) * c2) + ((((k1 >>> 16) * c2) & 0xffff) << 16)) & 0xffffffff;
        h1 ^= k1;
    }
    h1 ^= key.length;
    h1 ^= h1 >>> 16;
    h1 = (((h1 & 0xffff) * 0x85ebca6b) + ((((h1 >>> 16) * 0x85ebca6b) & 0xffff) << 16)) & 0xffffffff;
    h1 ^= h1 >>> 13;
    h1 = ((((h1 & 0xffff) * 0xc2b2ae35) + ((((h1 >>> 16) * 0xc2b2ae35) & 0xffff) << 16))) & 0xffffffff;
    h1 ^= h1 >>> 16;
    return h1 >>> 0;
  }

  root.app = app;
  return app;
})(this, $, _, Backbone);

(function(root, $, _, Backbone){
  app = root.app || {};

  app.ModalView = Backbone.View.extend({
    tagName: 'div',
    className: 'modal',
    template: _.template($('#tpl_modal').html()),
    events: {
      'click .submit': 'close'
    },
    initialize: function(options){
      this.options = options;
      this.callback = options.callback;
    },
    render: function(){
      this.$el.html(this.template(this.options));
      return this;
    },
    close: function(){
      _.isFunction(this.callback) && this.callback();
      this.remove();
    }
  });

  app.modal = function(options){
    var view = new app.ModalView(options);
    $('body').append(view.render().el);
  };

  root.app = app;
  return app;
})(window, $, _, Backbone);

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

(function(root, _, Backbone){
  app = root.app || {};

  app.RejectionView = Backbone.View.extend({
    render: function(){
      this.$el.html(this.template());
      return this;
    }
  });

  app.RejectionTooEarlyView = app.RejectionView.extend({
    template: _.template($('#tpl_too_early').html())
  });

  app.RejectionTooLateView = app.RejectionView.extend({
    template: _.template($('#tpl_too_late').html())
  });

  app.RejectionNoMoreChanceView = app.RejectionView.extend({
    template: _.template($('#tpl_no_more_chance').html())
  });

  app.WelcomeView = Backbone.View.extend({
    tagName: 'div',
    className: 'welcome',
    template: _.template($('#tpl_welcome').html()),
    events: {
      'click .submit': 'onSubmit',
    },
    initialize: function(options){
      this.content = options.content;
      this.infoFields = options.infoFields;
      this.quizId = options.quizId;
    },
    render: function(){
      this.$el.html(this.template({
        content: this.content,
        infoFields: this.infoFields
      }));
      return this;
    },
    onSubmit: function(e){
      var field_keys = _.unzip(this.infoFields)[0];
      var validated = false;
      var field_data = [];
      if (field_keys.length){
        validated = _(this.$('input')).chain()
        .filter(function(input){
          return _(field_keys).indexOf(input.name) >= 0;
        }).every(function(input){
          if (input.value.length > 0){
            field_data.push([input.name, input.value])
            localStorage.setItem(input.name, input.value);
            return true;
          }
          return false;
        }).value();
      } else {
        validated = true;
      }
      if(validated){
        this.trigger('startQuiz', field_data);
      } else {
        app.modal({
          message: "亲，需填完信息才能开始哦~",
          emotion: "tricky",
          button: { text: "关闭" }
        });
      }
    }
  });

  root.app = app;
  return app;
})(this, _, Backbone);

(function(root, _, Backbone){
  app = root.app || {};

  app.QuestionView = Backbone.View.extend({
    tagName: 'div',
    className: 'question',
    template: _.template($('#tpl_question').html()),
    events: {
      'click .submit': 'onSubmit'
    },
    initialize: function(options){
      // set code(A,B,C...) for each options and build a collection
      var optionData = this.model.get('options');
      var questionOptions =  new app.OptionCollection(optionData);
      questionOptions.each(function(model, index){
        model.set('code' , String.fromCharCode(65 + index));
      });
      this.model.set('options', questionOptions);
      this.listenTo(questionOptions, 'change:checked', this.toggleChecked);
      this.on('timeout', this.onTimeout, this);
      this.optionViews = [];
    },
    render: function(){
      var data = this.model.toJSON();
      this.$el.html(this.template(data));
      this.renderAllOptions();
      return this;
    },
    renderOption: function(model){
      if(this.model.get('type') == app.QUESTION_TYPE.MULTI){
        var ViewClass = app.MultiSelectionView
      } else {
        var ViewClass = app.SingleSelectionView
      }
      var view = new ViewClass({model:model});
      this.optionViews.push(view);
      this.$('.option_list').append(view.render().el);
    },
    renderAllOptions: function(){
      var questionOptions = _.shuffle(this.model.get('options').models);
      _.each(questionOptions, this.renderOption, this);
      return this;
    },
    toggleChecked: function(checked){
      if(this.model.get('type') == app.QUESTION_TYPE.MULTI){
        this.model.set('selected', this.model.get('options').filter('checked'))
      } else {
        this.model.set('selected', [ checked ])
      }
    },
    onSubmit: function(){
      if (_.isEmpty(this.model.get('selected'))) return false;
      this.finish();
    },
    onTimeout: function(){
      this.model.set('timeout', true);
      this.finish();
    },
    finish: function(){
      this.model.set('answered', true);
      this.trigger('finish', this.model);
    },
    close: function(){
      _.each(this.optionViews, function(view){ view.remove(); });
      this.remove();
    }
  });

  app.OptionView = Backbone.View.extend({
    tagName: 'div',
    className: 'question_option',
    events: {
      'change input': 'toggle'
    },
    render: function(){
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    toggle: function(){
      var checked = this.model.get('checked');
      this.model.set('checked', !checked);
    },
  });

  app.SingleSelectionView = app.OptionView.extend({
    template: _.template($('#tpl_option_single').html())
  });

  app.MultiSelectionView = app.OptionView.extend({
    template: _.template($('#tpl_option_multi').html())
  });

  root.app = app;
  return app;
})(this, _, Backbone);

(function(root, $, _, Backbone){

  app = root.app || {};

  app.QuizBaseView = Backbone.View.extend({
    tagName: 'div',
    className: 'quiz',
    template: _.template($('#tpl_quiz').html()),
    initialize: function(options){
      this.config = options.config;
      this.gameDataRoot = options.gameDataRoot;
      this.questions = new app.QuestionCollection();
    },
    render: function(){
      this.$el.html(this.template({timeLimit: this.timeLimit}));
      // Once get a question start the quiz
      this.listenToOnce(this.questions, 'add', this.start);
      this.listenTo(this.questions, 'change:answered', this.updatePanel);
      this.download();
      return this;
    },
    close: function(){
      this.questionView && this.questionView.close();
      this.remove();
    },
    download: function(){
      throw new Error('Not implemented');
    },
    start: function(){
      this.preQuiz && this.preQuiz();
      this.play();
    },
    play: function(){
      this.currentQuestion = _.sample(this.questions.filter({'answered': false}));
      this.preQuestion && this.preQuestion();
      this.questionView && this.questionView.remove();
      this.questionView = new app.QuestionView({model: this.currentQuestion});
      this.listenToOnce(this.questionView, 'finish', this.finishQuestion);
      this.$el.append(this.questionView.render().el);
      console.log(this.currentQuestion.getAnswerCodes().join());
    },
    timeLimit: function(){
      return this.config.time_per_question || null;
    },
    updatePanel: function(){
      var count = this.questions.filter({'answered': true}).length,
          questionPoints = this.config.question_points;
      var points = this.questions.totalPoints(questionPoints);
      this.$('#count').html(count);
      this.$('#points').html(points);
      console.log('update panel', count, points);
    },
    finishQuestion: function(){
      //Todo: ajax to server
      this.postQuestion && this.postQuestion();
      var current = this.currentQuestion,
          showAnswer = (this.config.show_answer || false),
          timeout = current.get('timeout'),
          message = current.isCorrect() ? '亲，答题正确，好厉害哦~' : (
            timeout ? '亲，回答超时，注意答题时间哦~' : '亲，答题错误。'
          ),
          emotion = timeout ? 'sweat' : (
            current.isCorrect() ? 'tongue' : 'tears'
          );
      showAnswer && (message += "正确答案:" + current.getAnswerCodes().join() + '。');
      if(this.hasNext()){
        app.modal({
          message: message,
          button: { text: "下一题" },
          emotion: emotion,
          callback: _.bind(this.play, this)
        });
      } else {
        this.postQuiz && this.postQuiz();
        app.modal({
          message: message + "游戏结束",
          button: { text: "查看结果" },
          emotion: emotion,
          callback: _.bind(function(){
            var points = this.questions.totalPoints(this.config.question_points);
            this.trigger('finishQuiz', points);
          }, this)
        });
      }
    },
    startTimer: function(){
      var counter = 0,
          timeLimit = this.timeLimit();
      this.updateTimer(timeLimit);
      var callback = function(){
        remaining = timeLimit - ++counter;
        this.updateTimer(remaining);
        if (remaining < 1) this.timeout();
      };
      this.timer = setInterval(_.bind(callback, this), 1000);
    },
    updateTimer: function(remaining){
      function formatSeconds(seconds){
        var minutes = parseInt(seconds / 60);
        var seconds = seconds % 60;
        return _.map([minutes, seconds], function(s){
          if (s > 9) return '' + s;
          return '0' + s;
        }).join(':');
      }
      this.$('#timer').html( formatSeconds(remaining) );
    },
    timeout: function(){
      this.clearTimer();
      this.questionView.trigger('timeout');
    },
    clearTimer: function(){
      this.timer && clearInterval(this.timer);
      this.timer = null;
    },
    hasNext: function(){
      throw new Error('Not implemented');
    }
  });

  app.OrdinaryQuizView = app.QuizBaseView.extend({
    preQuestion: function(){
      if(this.timeLimit()) this.startTimer();
    },
    postQuestion: function(){
      this.clearTimer();
    },
    download: _.throttle(function(){
      // save the unloaded files
      if(!this.unloadedFiles){
        var files = _.clone(this.config.question_files);
        this.unloadedFiles = _.mapObject(files, function(val){
          return _.shuffle(val);
        })
      }
      var loadedCount = this.questions.countBy('type');
      var neededType = _.findKey(this.config.count, function(count, type){
        var loaded = loadedCount[type] || 0;
        // console.log('type:' + type +' loaded:'+loaded+' need:'+count);
        return loaded < count;
      });
      if (!neededType) return this.questions;
      // download files only when internet is accessable
      if (navigator.onLine) {
        var neededCount = this.config.count[neededType] - (loadedCount[neededType] || 0);
        var file = this.unloadedFiles[neededType].pop();
        $.ajax({
          dataType: "json",
          url: this.gameDataRoot + file,
          timeout: app.DOWNLOAD_TIMEOUT
        }).done(_.bind(function(data){
          var toAdd = _.sample(data.objects, neededCount);
          this.questions.add(toAdd);
        }, this));
      }
      // download more
      this.download();
    }, app.DOWNLOAD_TIMEOUT),
    hasNext: function(){
      return this.questions.any({'answered': false});
    }
  });

  // for those modes which need to download questions continuously
  app.ContinuousQuizView = app.QuizBaseView.extend({
    download: _.throttle(function(){
      if(_.isEmpty(this.unloadedFiles)){
        var files = _.clone(this.config.question_files);
        this.unloadedFiles = _(files).chain().values().flatten().shuffle().value();
      }
      if (navigator.onLine) {
        var file = this.unloadedFiles.pop();
        $.ajax({
          dataType: "json",
          url: this.gameDataRoot + file,
          timeout: app.DOWNLOAD_TIMEOUT
        }).done(_.bind(function(data){
          this.questions.add(data.objects);
        }, this));
      }
    }, app.DOWNLOAD_TIMEOUT),
    postQuestion: function(){
      var unanswered = this.questions.filter({'answered': false});
      if(unanswered.length < app.DOWNLOAD_TRIGGER) this.download();
    },
  });

  app.TimeLimitQuizView = app.ContinuousQuizView.extend({
    timeLimit: function(){
      return this.config.time_per_quiz || 300;
    },
    preQuiz: function(){
      if(this.timeLimit()) this.startTimer();
      this.startTime = new Date();
    },
    postQuiz: function(){
      this.clearTimer();
    },
    hasNext: function(){
      var limit = this.timeLimit();
          current = new Date();
      console.log('time limit', limit, (current - this.startTime)/1000);
      return current - this.startTime < limit * 1000;
    }
  });

  app.ChallengeQuizView = app.ContinuousQuizView.extend({
    timeLimit: function(){
      return null;
    },
    hasNext: function(){
      return this.currentQuestion.isCorrect();
    }
  });

  root.app = app;
  return app;
})(this, $, _, Backbone);

(function(root, _, Backbone){
  app = root.app || {};

  app.RankView = Backbone.View.extend({
    tagName: 'div',
    className: 'rank',
    template: _.template($('#tpl_rank').html()),
    events: {'click .submit': 'onSubmit'},
    initialize: function(options) {
      console.log(options);
      this.result = options.result;
    },
    render: function(){
      this.$el.html(this.template(this.result));
      return this;
    },
    onSubmit: function(){
      this.trigger('rerun');
    }
  });

  root.app = app;
  return app;
})(this, _, Backbone);

//# sourceMappingURL=packed.js.map
