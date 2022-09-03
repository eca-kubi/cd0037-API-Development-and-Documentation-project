from flask import Flask, request, abort, jsonify
from flask_cors import CORS

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app=app, resources={r"/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories')
    def get_categories():
        try:
            categories = Category.query.all()
            formatted_categories = [category.format() for category in categories]
            return jsonify({
                "success": True,
                "categories": formatted_categories
            })
        except Exception as err:
            abort(422)


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    def paginate_questions(selection, page):
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions

    @app.route('/questions')
    def get_questions():
        try:
            page = request.args.get("page", 1, type=int)
            questions = Question.query.all()
            page_questions = paginate_questions(questions, page)
            if len(page_questions) == 0:
                abort(404)
            # categories = [value[0] for value in db.session.query(Category.type)]
            categories = [category.format() for category in Category.query.all()]
            return jsonify({
                "success": True,
                "questions": page_questions,
                "total_questions": len(questions),
                "categories": categories,
                "current_category": None
            })
        except Exception as err:
            abort(422)

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter_by(id=question_id).one_or_none()

            question.delete()

            # questions = [question.format() for question in Question.query.all()]

            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except Exception as err:
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            body = request.get_json()
            question = Question(
                question=body.get('question'),
                answer=body.get('answer'),
                category=body.get('category'),
                difficulty=body.get('difficulty')
            )
            question.insert()
            return jsonify({
                "success": True,
                "question": question.format()
            })
        except Exception as err:
            db.session.rollback()
            abort(400)
        finally:
            db.session.close()

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/search-questions', methods=['POST'])
    def search_questions():
        try:
            search_term = request.get_json()['search_term']
            questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
            formatted_questions = [question.format() for question in questions]
            return jsonify({
                "success": True,
                "questions": formatted_questions,
                "total_questions": len(formatted_questions),
                "current_category": None
            })
        except Exception as err:
            abort(422)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        try:
            page = request.args.get("page", 1, type=int)
            category = Category.query.filter(Category.id == category_id).one_or_none()
            if category is None:
                abort(404)
            questions = Question.query.filter(Question.category == category_id).all()
            paginated_questions = paginate_questions(questions, page)
            return jsonify({
                "success": True,
                "questions": paginated_questions,
                "total_questions": len(questions),
                "current_category": category_id
            })
        except Exception as err:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        try:
            data = request.get_json()
            previous_questions = data["previous_questions"]
            quiz_category = data["quiz_category"]
            print(quiz_category)
            if quiz_category == 0:
                question = Question.query.filter(Question.id.notin_(previous_questions)).first()
            else:
                question = Question.query.filter(Question.id.notin_(previous_questions)) \
                    .filter_by(category=quiz_category) \
                    .first()

            return jsonify({
                "success": True,
                "question": question.format() if question else None
            })
        except Exception as err:
            abort(422)


    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )

    @app.errorhandler(500)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 500, "message": "server encountered an error"}),
            500,
        )

    return app
